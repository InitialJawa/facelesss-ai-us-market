from .base import Stage, StageContext
from loguru import logger


class AssetStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Gathering assets for: {ctx.topic}")

        ctx["assets"] = {
            "backgrounds": [],
            "brolls": [],
            "overlays": [],
        }

        return ctx
