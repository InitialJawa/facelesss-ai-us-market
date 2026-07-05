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
from pipeline.interfaces.llm import OpenAILlmProvider
from pipeline.interfaces.tts import EdgeTTSProvider
from pipeline.interfaces.storage import LocalStorageProvider
from brain.manager import Brain
from renderer.engine import RenderEngine
from app.config import settings


class PipelineOrchestrator:
    def __init__(self, brain: Brain, queue: PipelineQueue):
        self.brain = brain
        self.queue = queue
        self.llm = OpenAILlmProvider(
            api_key=settings.openai_api_key if settings.openai_api_key else None,
            model=settings.openai_model,
        )
        self.tts = EdgeTTSProvider()
        self.storage = LocalStorageProvider(base_path=settings.assets_dir)
        self.renderer = RenderEngine(output_dir=settings.output_dir)

        self.stages = {
            "researching": ResearchStage(),
            "writing": WritingStage(llm_provider=self.llm),
            "voicing": VoiceStage(tts_provider=self.tts),
            "assembling": AssetStage(render_engine=self.renderer),
            "rendering": RenderStage(render_engine=self.renderer),
            "thumbnailing": ThumbnailStage(),
            "uploading": UploadStage(youtube_client=None),
        }
        self._running = False

    def create_job(self, topic: str, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        ctx = StageContext({
            "job_id": job_id,
            "topic": topic,
            "output_dir": settings.output_dir,
            "assets_dir": settings.assets_dir,
            **kwargs,
        })
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

        ctx_data = job.get("context", {})
        if isinstance(ctx_data, str):
            ctx_data = json.loads(ctx_data)

        ctx = StageContext({
            **ctx_data,
            "_brain": self.brain,
            "_queue": self.queue,
            "job_id": job_id,
            "topic": job["topic"],
            "output_dir": settings.output_dir,
            "assets_dir": settings.assets_dir,
        })

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
                logger.exception(f"Stage {stage_key} failed for job {job_id}")
                self.queue.fail(job_id, str(e))
                return False

        brain = self.brain
        if ctx.get("video_info"):
            video_info = ctx["video_info"]
            brain.learn("performance", {
                "avg_render_time": video_info.get("duration", 30),
            })

        video_memory = brain.memory.get("video_memory", {})
        brain.set("video_memory", "total_generated",
                  video_memory.get("total_generated", 0) + 1)
        brain.set("video_memory", "total_uploaded",
                  video_memory.get("total_uploaded", 0) + 1)

        return True

    async def process_pending(self, limit: int = 5) -> list[tuple[str, bool]]:
        jobs = self.queue.dequeue(limit)
        results = []
        for job in jobs:
            logger.info(f"Processing job: {job['id']} - {job['topic']}")
            success = await self.process_job(job["id"])
            results.append((job["id"], success))
            logger.info(f"Job {job['id']}: {'✓' if success else '✗'}")
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
