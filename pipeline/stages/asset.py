import os
import uuid
from .base import Stage, StageContext
from loguru import logger


class AssetStage(Stage):
    def __init__(self, render_engine=None):
        super().__init__()
        self.renderer = render_engine

    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Gathering assets for: {ctx.topic}")

        script = ctx.script or {}
        scenes = script.get("scenes", [])
        output_dir = ctx.get("assets_dir", "./assets/scenes")
        os.makedirs(output_dir, exist_ok=True)

        image_paths = []
        durations = []
        scene_data = []

        for i, scene in enumerate(scenes):
            desc = scene.get("visual_desc", ctx.topic)
            duration = scene.get("duration", 5)
            img_path = os.path.join(output_dir, f"scene_{ctx.job_id[:8]}_{i:02d}.jpg")

            try:
                self.renderer.generate_background(desc, img_path)
            except Exception as e:
                logger.warning(f"Background gen failed: {e}, creating fallback")
                self.renderer.generate_background(ctx.topic, img_path)

            if scene.get("narration"):
                text_path = img_path.replace(".jpg", "_text.png")
                try:
                    self.renderer.create_text_overlay(
                        scene["narration"][:100], text_path
                    )
                    image_paths.append(text_path)
                    durations.append(min(duration * 0.4, 3.0))
                except Exception:
                    pass

            image_paths.append(img_path)
            durations.append(duration)

            scene_data.append({
                "order": i + 1,
                "narration": scene.get("narration", ""),
                "visual_desc": desc,
                "image_path": img_path,
                "duration": duration,
            })

        ctx["assets"] = {
            "scene_data": scene_data,
            "image_paths": image_paths,
            "durations": durations,
            "total_duration": sum(durations),
        }

        logger.info(f"Assets ready: {len(image_paths)} images")
        return ctx
