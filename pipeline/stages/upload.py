from datetime import datetime
from .base import Stage, StageContext
from loguru import logger


class UploadStage(Stage):
    def __init__(self, youtube_client=None):
        super().__init__()
        self.youtube = youtube_client

    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Upload stage: {ctx.job_id} (simulated)")

        video_path = ctx.video_path
        thumbnail_path = ctx.thumbnail_path
        script = ctx.script or {}

        ctx.youtube_id = "SIMULATED_UPLOAD"
        ctx["upload_result"] = {
            "status": "simulated",
            "message": "Upload simulated - set YouTube API keys to enable real upload",
            "youtube_id": None,
        }

        return ctx
