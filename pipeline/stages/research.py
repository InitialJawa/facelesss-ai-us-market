from .base import Stage, StageContext
from loguru import logger


class ResearchStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Researching topic: {ctx.topic}")
        brain = ctx.brain

        suggestions = brain.suggest_hook()
        avoid = brain.avoid_words()
        niche = ctx.get("niche", "general")

        ctx["research"] = {
            "topic": ctx.topic,
            "suggested_hook": suggestions,
            "avoid_words": avoid,
            "niche": niche,
            "voice": brain.suggest_voice(),
            "duration": brain.suggest_duration() or 30,
        }

        return ctx
