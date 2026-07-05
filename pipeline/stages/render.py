import os
import uuid
from .base import Stage, StageContext
from loguru import logger


class RenderStage(Stage):
    def __init__(self, render_engine=None):
        super().__init__()
        self.renderer = render_engine

    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Rendering video for: {ctx.job_id}")

        assets = ctx.get("assets", {})
        image_paths = assets.get("image_paths", [])
        durations = assets.get("durations", [])
        audio_path = ctx.audio_path

        if not image_paths:
            logger.warning("No images to render, creating placeholder")
            placeholder = os.path.join(ctx.get("assets_dir", "./assets"), f"placeholder_{ctx.job_id[:8]}.jpg")
            self.renderer.generate_background(ctx.topic, placeholder)
            image_paths = [placeholder]
            durations = [30]

        output_filename = f"video_{ctx.job_id[:8]}.mp4"
        output_path = self.renderer.render_video(
            audio_path=audio_path,
            image_paths=image_paths,
            durations=durations,
            output_path=output_filename,
        )

        info = self.renderer.get_video_info(output_path)
        ctx.video_path = output_path
        ctx["video_info"] = info

        logger.info(f"Video rendered: {output_path} ({info.get('size_mb', 0)}MB, {info.get('duration', 0)}s)")
        return ctx
