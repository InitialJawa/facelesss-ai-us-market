from abc import ABC, abstractmethod
from typing import Any
from loguru import logger


class StageContext(dict):
    @property
    def job_id(self) -> str:
        return self.get("job_id", "")

    @property
    def topic(self) -> str:
        return self.get("topic", "")

    @property
    def video_id(self) -> str | None:
        return self.get("video_id")

    @video_id.setter
    def video_id(self, value: str):
        self["video_id"] = value

    @property
    def script_id(self) -> str | None:
        return self.get("script_id")

    @script_id.setter
    def script_id(self, value: str):
        self["script_id"] = value

    @property
    def script(self) -> dict | None:
        return self.get("script")

    @script.setter
    def script(self, value: dict):
        self["script"] = value

    @property
    def voice_id(self) -> str | None:
        return self.get("voice_id")

    @voice_id.setter
    def voice_id(self, value: str):
        self["voice_id"] = value

    @property
    def audio_path(self) -> str | None:
        return self.get("audio_path")

    @audio_path.setter
    def audio_path(self, value: str):
        self["audio_path"] = value

    @property
    def video_path(self) -> str | None:
        return self.get("video_path")

    @video_path.setter
    def video_path(self, value: str):
        self["video_path"] = value

    @property
    def thumbnail_path(self) -> str | None:
        return self.get("thumbnail_path")

    @thumbnail_path.setter
    def thumbnail_path(self, value: str):
        self["thumbnail_path"] = value

    @property
    def youtube_id(self) -> str | None:
        return self.get("youtube_id")

    @youtube_id.setter
    def youtube_id(self, value: str):
        self["youtube_id"] = value

    @property
    def brain(self) -> Any:
        return self.get("_brain")

    @property
    def db(self) -> Any:
        return self.get("_db")

    @property
    def queue(self) -> Any:
        return self.get("_queue")


class Stage(ABC):
    def __init__(self):
        self.name = self.__class__.__name__.replace("Stage", "").lower()

    @abstractmethod
    async def execute(self, ctx: StageContext) -> StageContext: ...

    async def __call__(self, ctx: StageContext) -> StageContext:
        logger.info(f"Stage [{self.name}] executing for job {ctx.job_id}")
        try:
            result = await self.execute(ctx)
            logger.info(f"Stage [{self.name}] completed for job {ctx.job_id}")
            return result
        except Exception as e:
            logger.error(f"Stage [{self.name}] failed for job {ctx.job_id}: {e}")
            raise
