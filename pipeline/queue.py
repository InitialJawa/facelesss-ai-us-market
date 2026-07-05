import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from loguru import logger


STAGES = [
    "pending",
    "researching",
    "writing",
    "voicing",
    "assembling",
    "rendering",
    "thumbnailing",
    "uploading",
    "done",
]

STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}


class PipelineQueue:
    def __init__(self, db_path: str = "./pipeline/queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=5000")
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                stage TEXT NOT NULL DEFAULT 'pending',
                status TEXT NOT NULL DEFAULT 'pending',
                context TEXT NOT NULL DEFAULT '{}',
                priority INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_stage ON queue(stage)
        """)
        conn.commit()

    def enqueue(self, job_id: str, topic: str, context: dict | None = None) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO queue
               (id, topic, stage, status, context, priority, created_at, updated_at)
               VALUES (?, ?, 'pending', 'pending', ?, 0, ?, ?)""",
            (job_id, topic, json.dumps(context or {}), now, now),
        )
        conn.commit()
        logger.info(f"Queue: {job_id} enqueued for '{topic}'")

    def dequeue(self, batch_size: int = 5) -> list[dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM queue
               WHERE status = 'pending'
               ORDER BY priority DESC, created_at ASC
               LIMIT ?""",
            (batch_size,),
        ).fetchall()
        conn.execute(
            """UPDATE queue SET status = 'in_progress', started_at = ?, updated_at = ?
               WHERE status = 'pending'
               AND id IN ({})""".format(
                ",".join("?" for _ in rows)
            ),
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
            + tuple(r["id"] for r in rows),
        )
        conn.commit()
        return [dict(r) for r in rows]

    def advance(self, job_id: str, next_stage: str) -> None:
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        status = "done" if next_stage == "done" else "in_progress"
        conn.execute(
            """UPDATE queue
               SET stage = ?, status = ?, updated_at = ?,
                   completed_at = CASE WHEN ? = 'done' THEN ? ELSE NULL END
               WHERE id = ?""",
            (next_stage, status, now, next_stage, now, job_id),
        )
        conn.commit()
        logger.info(f"Queue: {job_id} → {next_stage}")

    def fail(self, job_id: str, error: str) -> None:
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        row = conn.execute(
            "SELECT retry_count FROM queue WHERE id = ?", (job_id,)
        ).fetchone()
        retries = (row["retry_count"] if row else 0) + 1
        conn.execute(
            """UPDATE queue
               SET status = 'failed', error_message = ?, retry_count = ?,
                   updated_at = ?
               WHERE id = ?""",
            (error, retries, now, job_id),
        )
        conn.commit()
        logger.error(f"Queue: {job_id} FAILED (x{retries}): {error[:100]}")

    def reset(self, job_id: str, stage: str | None = None) -> None:
        conn = self._get_conn()
        target_stage = stage or "pending"
        now = datetime.utcnow().isoformat()
        conn.execute(
            """UPDATE queue
               SET stage = ?, status = 'pending', error_message = NULL,
                   updated_at = ?, started_at = NULL, completed_at = NULL
               WHERE id = ?""",
            (target_stage, now, job_id),
        )
        conn.commit()
        logger.info(f"Queue: {job_id} reset to {target_stage}")

    def resume_all(self) -> list[dict[str, Any]]:
        conn = self._get_conn()
        interrupted = conn.execute(
            """SELECT * FROM queue
               WHERE status = 'in_progress'
               ORDER BY updated_at ASC"""
        ).fetchall()
        for row in interrupted:
            self.reset(row["id"])
        pending = conn.execute(
            """SELECT * FROM queue
               WHERE status = 'pending'
               ORDER BY priority DESC, created_at ASC"""
        ).fetchall()
        if interrupted:
            logger.info(
                f"Queue: {len(interrupted)} jobs reset for resume"
            )
        logger.info(f"Queue: {len(pending)} jobs ready to process")
        return [dict(r) for r in pending]

    def get_status(self) -> dict[str, int]:
        conn = self._get_conn()
        counts = conn.execute(
            """SELECT status, COUNT(*) as cnt FROM queue GROUP BY status"""
        ).fetchall()
        result = {"total": 0}
        for row in counts:
            result[row["status"]] = row["cnt"]
            result["total"] += row["cnt"]
        return result

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM queue WHERE id = ?", (job_id,)
        ).fetchone()
        return dict(row) if row else None

    def cancel(self, job_id: str) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE queue SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), job_id),
        )
        conn.commit()
        logger.info(f"Queue: {job_id} cancelled")

    def cleanup(self, max_age_hours: int = 72) -> int:
        conn = self._get_conn()
        cutoff = datetime.utcnow().timestamp() - max_age_hours * 3600
        conn.execute(
            "DELETE FROM queue WHERE status IN ('done', 'cancelled') AND "
            "created_at < ?",
            (datetime.utcfromtimestamp(cutoff).isoformat(),),
        )
        conn.commit()
        deleted = conn.total_changes
        logger.info(f"Queue: cleaned up {deleted} old jobs")
        return deleted
