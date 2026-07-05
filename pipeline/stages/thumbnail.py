from .base import Stage, StageContext
from loguru import logger


class ThumbnailStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Generating thumbnail for: {ctx.job_id}")

        ctx.thumbnail_path = None

        return ctx
