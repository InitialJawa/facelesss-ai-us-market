from abc import ABC, abstractmethod
from typing import Any


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self, text: str, *, voice: str = "id-ID-ArdiNeural",
        speed: float = 1.0, output_path: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_available_voices(
        self, language: str | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_voice_preview(self, voice: str) -> str: ...
