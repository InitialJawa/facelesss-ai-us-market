from datetime import datetime
from .base import Stage, StageContext
from loguru import logger


class UploadStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Uploading video: {ctx.job_id}")

        ctx.youtube_id = None

        return ctx
