from .base import Stage, StageContext
from loguru import logger


class VoiceStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Generating voice for: {ctx.job_id}")

        brain = ctx.brain
        voice = ctx.get("voice", brain.suggest_voice())

        ctx.voice_id = voice
        ctx.audio_path = None

        return ctx
