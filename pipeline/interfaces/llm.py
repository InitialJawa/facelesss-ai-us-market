from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def generate_script(
        self, topic: str, *, duration: int = 30, language: str = "id",
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
