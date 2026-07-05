from datetime import datetime
from .base import Stage, StageContext
from loguru import logger


class WritingStage(Stage):
    def __init__(self, llm_provider=None):
        super().__init__()
        self.llm = llm_provider

    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Writing script for: {ctx.topic}")

        brain = ctx.brain
        research = ctx.get("research", {})
        duration = research.get("duration", 30)
        hook_type = research.get("suggested_hook", "question")
        avoid = research.get("avoid_words", [])
        niche = research.get("niche", "general")

        script = await self.llm.generate_script(
            topic=ctx.topic,
            duration=duration,
            language="en",
            avoid_words=avoid,
            hook_type=hook_type,
            tone="informative",
        )

        ctx.script = {
            "title": script.get("title", ctx.topic),
            "content": script.get("hook_text", ""),
            "hook_type": script.get("hook", hook_type),
            "hook_text": script.get("hook_text", ""),
            "scenes": script.get("scenes", []),
            "word_count": script.get("word_count", 150),
            "duration": duration,
            "tone": "informative",
            "niche": niche,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return ctx
