import asyncio
import json
import uuid
from typing import Any
from loguru import logger

from pipeline.queue import PipelineQueue
from pipeline.stages.base import StageContext
from pipeline.stages import (
    ResearchStage, WritingStage, VoiceStage, AssetStage,
    RenderStage, ThumbnailStage, UploadStage,
)
from brain.manager import Brain


class PipelineOrchestrator:
    def __init__(self, brain: Brain, queue: PipelineQueue):
        self.brain = brain
        self.queue = queue
        self.stages = {
            "researching": ResearchStage(),
            "writing": WritingStage(),
            "voicing": VoiceStage(),
            "assembling": AssetStage(),
            "rendering": RenderStage(),
            "thumbnailing": ThumbnailStage(),
            "uploading": UploadStage(),
        }
        self._running = False

    def create_job(self, topic: str, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        ctx = StageContext(
            {"job_id": job_id, "topic": topic, "_brain": self.brain, **kwargs}
        )
        self.queue.enqueue(job_id, topic, dict(ctx))
        return job_id

    async def process_job(self, job_id: str) -> bool:
        job = self.queue.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        current_stage = job["stage"]
        if current_stage == "done":
            return True

        ctx = StageContext(
            {**(json.loads(job["context"]) if isinstance(job.get("context"), str) else job.get("context", {})),
             "_brain": self.brain, "_queue": self.queue}
        )
        ctx["job_id"] = job_id
        ctx["topic"] = job["topic"]

        stage_keys = list(self.stages.keys())
        start_index = stage_keys.index(current_stage) if current_stage in stage_keys else 0

        for i in range(start_index, len(stage_keys)):
            stage_key = stage_keys[i]
            stage = self.stages[stage_key]

            try:
                ctx = await stage(ctx)
                next_stage = stage_keys[i + 1] if i + 1 < len(stage_keys) else "done"
                self.queue.advance(job_id, next_stage)
            except Exception as e:
                self.queue.fail(job_id, str(e))
                return False

        return True

    async def process_pending(self, limit: int = 5) -> list[str]:
        jobs = self.queue.dequeue(limit)
        results = []
        for job in jobs:
            success = await self.process_job(job["id"])
            results.append((job["id"], success))
        return results

    async def run_continuous(self, interval: int = 30):
        self._running = True
        logger.info(f"Orchestrator running continuously (interval={interval}s)")
        while self._running:
            try:
                pending = self.queue.get_status().get("pending", 0)
                if pending > 0:
                    await self.process_pending(min(pending, 5))
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await asyncio.sleep(10)

    def stop(self):
        self._running = False

    def get_status_summary(self) -> dict[str, Any]:
        queue_status = self.queue.get_status()
        return {
            "queue": queue_status,
            "brain_modules": list(self.brain.memory.keys()),
        }
