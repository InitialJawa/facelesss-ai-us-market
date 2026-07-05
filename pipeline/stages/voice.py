import os
import uuid
from .base import Stage, StageContext
from loguru import logger


class VoiceStage(Stage):
    def __init__(self, tts_provider=None):
        super().__init__()
        self.tts = tts_provider

    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Generating voice for: {ctx.job_id}")

        brain = ctx.brain
        script = ctx.script or {}
        scenes = script.get("scenes", [])

        full_text = "\n".join(
            s.get("narration", "") for s in scenes
        )
        if not full_text:
            full_text = script.get("hook_text", ctx.topic)

        voice = brain.suggest_voice()
        if "US" not in voice and "US" not in voice:
            voice = "en-US-ChristopherNeural"

        output_dir = ctx.get("output_dir", "./voices")
        os.makedirs(output_dir, exist_ok=True)
        audio_path = os.path.join(output_dir, f"voice_{uuid.uuid4().hex[:8]}.mp3")

        result = await self.tts.synthesize(
            text=full_text,
            voice=voice,
            speed=1.0,
            output_path=audio_path,
        )

        ctx.voice_id = voice
        ctx.audio_path = result["path"]
        ctx["audio_duration"] = result.get("duration", 0)

        logger.info(f"Voice generated: {result['path']} ({result.get('duration', 0)}s)")
        return ctx
