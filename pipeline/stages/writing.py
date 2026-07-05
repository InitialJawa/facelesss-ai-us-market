from datetime import datetime
from .base import Stage, StageContext
from loguru import logger


class WritingStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Writing script for: {ctx.topic}")

        brain = ctx.brain
        duration = ctx.get("duration", brain.suggest_duration())
        hook_type = ctx.get("hook_type", brain.suggest_hook())
        avoid = brain.avoid_words()

        research = ctx.get("research", {})

        ctx.script = {
            "title": ctx.topic,
            "content": f"Script placeholder for: {ctx.topic}",
            "hook_type": hook_type,
            "word_count": 150,
            "duration": duration,
            "tone": "informative",
            "avoid_words": avoid,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return ctx
