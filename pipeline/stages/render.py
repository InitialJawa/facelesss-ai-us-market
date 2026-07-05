from .base import Stage, StageContext
from loguru import logger


class RenderStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Rendering video for: {ctx.job_id}")

        ctx.video_path = None

        return ctx
