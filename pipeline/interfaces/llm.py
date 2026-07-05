from abc import ABC, abstractmethod
from typing import Any
import random


class LLMProvider(ABC):
    @abstractmethod
    async def generate_script(
        self, topic: str, *, duration: int = 30, language: str = "en",
        avoid_words: list[str] | None = None, hook_type: str | None = None,
        tone: str = "informative",
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def suggest_topics(
        self, niche: str, count: int = 10,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def optimize_hook(
        self, script: str, hook_type: str | None = None,
    ) -> str: ...

    @abstractmethod
    async def generate_description(
        self, title: str, content: str,
    ) -> str: ...

    @abstractmethod
    async def generate_tags(
        self, title: str, niche: str, count: int = 10,
    ) -> list[str]: ...

    @abstractmethod
    async def analyze_performance(
        self, analytics_data: dict[str, Any],
    ) -> dict[str, Any]: ...


class OpenAILlmProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _ensure_client(self):
        if self._client is None and self.api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)

    async def _call_llm(self, system: str, prompt: str) -> str:
        await self._ensure_client()
        if self._client:
            try:
                resp = await self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                )
                return resp.choices[0].message.content or ""
            except Exception:
                pass
        return ""

    async def generate_script(
        self, topic: str, *, duration: int = 30, language: str = "en",
        avoid_words: list[str] | None = None, hook_type: str | None = None,
        tone: str = "informative",
    ) -> dict[str, Any]:
        system = "You are a professional script writer for YouTube videos."
        prompt = (
            f"Write a {duration}-second script in {language} about '{topic}'.\n"
            f"Tone: {tone}.\n"
            f"Avoid words: {avoid_words or []}.\n"
            f"Hook style: {hook_type or 'question'}.\n"
            "Return JSON: {\"hook\": \"...\", \"hook_text\": \"...\", "
            "\"scenes\": [{\"order\": 1, \"narration\": \"...\", "
            "\"visual_desc\": \"...\", \"duration\": 5}], "
            "\"title\": \"...\", \"word_count\": 150}"
        )
        result = await self._call_llm(system, prompt)
        if result:
            try:
                import json
                return json.loads(result)
            except json.JSONDecodeError:
                pass
        return _fallback_script(topic, duration, language)

    async def suggest_topics(
        self, niche: str, count: int = 10,
    ) -> list[dict[str, Any]]:
        system = "You are a YouTube trend researcher."
        prompt = (
            f"Suggest {count} video topics in the '{niche}' niche for US market.\n"
            "Return JSON array: [{\"title\": \"...\", \"reason\": \"...\", "
            "\"estimated_competition\": \"low|medium|high\"}]"
        )
        result = await self._call_llm(system, prompt)
        if result:
            try:
                import json
                return json.loads(result)
            except json.JSONDecodeError:
                pass
        return [
            {"title": f"{niche} tip #{i+1}", "reason": "Popular niche",
             "estimated_competition": "medium"}
            for i in range(count)
        ]

    async def optimize_hook(
        self, script: str, hook_type: str | None = None,
    ) -> str:
        system = "You are a hook optimization expert."
        prompt = f"Rewrite the first 15 seconds as a {hook_type or 'question'}-style hook:\n\n{script[:500]}"
        result = await self._call_llm(system, prompt)
        return result or script[:200]

    async def generate_description(
        self, title: str, content: str,
    ) -> str:
        system = "You write YouTube video descriptions."
        prompt = (
            f"Write a description for '{title}'.\nContent: {content[:300]}...\n"
            "Include: summary, 3 key points, and a call to action."
        )
        result = await self._call_llm(system, prompt)
        return result or f"Check out this video about {title}!"

    async def generate_tags(
        self, title: str, niche: str, count: int = 10,
    ) -> list[str]:
        system = "You generate YouTube SEO tags."
        prompt = f"Generate {count} SEO tags for a video titled '{title}' in '{niche}' niche."
        result = await self._call_llm(system, prompt)
        if result:
            return [t.strip() for t in result.split(",") if t.strip()][:count]
        return [title.lower().replace(" ", ""), niche]

    async def analyze_performance(
        self, analytics_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {"suggestion": "No analysis available"}


def _fallback_script(topic: str, duration: int = 30, language: str = "en") -> dict[str, Any]:
    """Generate a script without API keys using templates."""
    import math
    scenes_count = max(3, duration // 7)
    words_per_scene = max(20, int(duration * 2.5 / scenes_count))

    hooks = [
        "question", "statistic", "story", "controversial",
        "benefit", "curiosity", "problem", "myth"
    ]
    hook = random.choice(hooks)
    hook_templates = {
        "question": f"Have you ever wondered why {topic.lower()} matters more than you think?",
        "statistic": f"Here's a shocking fact: {random.randint(60, 99)}% of people don't know this about {topic.lower()}.",
        "story": f"Let me tell you a story about how {topic.lower()} changed everything.",
        "controversial": f"Most people are wrong about {topic.lower()}. Here's the truth.",
        "benefit": f"Want to master {topic.lower()}? Start with this one simple trick.",
        "curiosity": f"The hidden secrets of {topic.lower()} that nobody talks about.",
        "problem": f"Struggling with {topic.lower()}? Here's what you're doing wrong.",
        "myth": f"Everything you know about {topic.lower()} is a lie.",
    }
    hook_text = hook_templates.get(hook, hook_templates["question"])

    scenes = []
    total_words = 0
    for i in range(scenes_count):
        scene_words = words_per_scene + random.randint(-5, 5)
        total_words += scene_words
        visuals = [
            f"Stock footage of {topic.lower()} in action",
            f"Animation explaining {topic.lower()} concept",
            f"Text overlay with key statistics about {topic.lower()}",
            f"Real-world example of {topic.lower()}",
            f"Expert talking head about {topic.lower()}",
            f"Graph showing {topic.lower()} trends",
            f"Comparison of {topic.lower()} methods",
            f"Close-up demonstration of {topic.lower()}",
            f"B-roll of people using {topic.lower()}",
            f"Transition scene with {topic.lower()} summary",
        ]
        scenes.append({
            "order": i + 1,
            "narration": (
                f"Point {i+1}: When it comes to {topic.lower()}, "
                f"there are several key factors to consider. "
                f"This is important because it affects how we understand "
                f"the bigger picture." if i > 0 else hook_text
            ),
            "visual_desc": random.choice(visuals),
            "duration": max(3, min(10, duration // scenes_count)),
            "asset_query": topic.lower(),
        })

    title_templates = [
        f"{topic}: The Ultimate Guide",
        f"10 Things You Didn't Know About {topic}",
        f"Why {topic} Matters in 2026",
        f"The Truth About {topic} Nobody Talks About",
        f"Master {topic} in 5 Minutes",
        f"{topic} Explained Simply",
        f"How {topic} Is Changing Everything",
        f"What Experts Say About {topic}",
    ]

    return {
        "hook": hook,
        "hook_text": hook_text,
        "scenes": scenes,
        "title": random.choice(title_templates),
        "word_count": total_words,
    }
