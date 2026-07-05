from abc import ABC, abstractmethod
from typing import Any
import os
import edge_tts
from loguru import logger


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self, text: str, *, voice: str = "en-US-ChristopherNeural",
        speed: float = 1.0, output_path: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_available_voices(
        self, language: str | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_voice_preview(self, voice: str) -> str: ...


class EdgeTTSProvider(TTSProvider):
    def __init__(self):
        self._voices_cache: list[dict[str, Any]] | None = None

    async def synthesize(
        self, text: str, *, voice: str = "en-US-ChristopherNeural",
        speed: float = 1.0, output_path: str | None = None,
    ) -> dict[str, Any]:
        if output_path is None:
            import uuid
            output_path = f"/tmp/tts_{uuid.uuid4().hex[:8]}.mp3"

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        rate_str = f"+{int((speed-1)*100)}%" if speed > 1 else "+0%"
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate_str)
        await communicate.save(output_path)

        import math
        duration = await self._get_duration(output_path)
        return {
            "path": output_path,
            "duration": duration,
            "voice": voice,
            "text_length": len(text),
        }

    async def _get_duration(self, audio_path: str) -> float:
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                 audio_path],
                capture_output=True, text=True, timeout=10,
            )
            return float(result.stdout.strip())
        except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
            return 0.0

    async def get_available_voices(
        self, language: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._voices_cache is None:
            voices = await edge_tts.list_voices()
            self._voices_cache = [
                {"id": v["Name"], "name": v["FriendlyName"],
                 "locale": v["Locale"], "gender": v["Gender"]}
                for v in voices
            ]
        if language:
            return [v for v in self._voices_cache if v["locale"].startswith(language)]
        return self._voices_cache

    async def get_voice_preview(self, voice: str) -> str:
        return f"Voice: {voice}"


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None

    async def _ensure_client(self):
        if self._client is None and self.api_key:
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)

    async def synthesize(
        self, text: str, *, voice: str = "21m00Tcm4TlvDq8ikWAM",
        speed: float = 1.0, output_path: str | None = None,
    ) -> dict[str, Any]:
        await self._ensure_client()
        if output_path is None:
            import uuid
            output_path = f"/tmp/tts_{uuid.uuid4().hex[:8]}.mp3"

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if self._client:
            try:
                audio = self._client.generate(text=text, voice=voice)
                import elevenlabs
                elevenlabs.save(audio, output_path)
                duration = 0.0
                return {"path": output_path, "duration": duration, "voice": voice, "text_length": len(text)}
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed: {e}, falling back to edge-tts")

        provider = EdgeTTSProvider()
        return await provider.synthesize(text, voice="en-US-ChristopherNeural", speed=speed, output_path=output_path)

    async def get_available_voices(
        self, language: str | None = None,
    ) -> list[dict[str, Any]]:
        await self._ensure_client()
        if self._client:
            try:
                voices = self._client.voices.get_all()
                return [{"id": v.voice_id, "name": v.name, "locale": v.labels.get("locale", ""), "gender": ""} for v in voices]
            except Exception:
                pass
        provider = EdgeTTSProvider()
        return await provider.get_available_voices(language)

    async def get_voice_preview(self, voice: str) -> str:
        return f"Voice ID: {voice}"
