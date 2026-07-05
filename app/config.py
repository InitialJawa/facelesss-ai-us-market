from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/faceless_ai"

    # LLM
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # TTS
    tts_provider: Literal["edge", "elevenlabs"] = "edge"
    elevenlabs_api_key: str = ""
    default_voice: str = "id-ID-ArdiNeural"

    # YouTube
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""
    youtube_channel_id: str = ""

    # Paths
    output_dir: str = "./output"
    assets_dir: str = "./assets"
    voices_dir: str = "./voices"
    templates_dir: str = "./templates"
    brain_dir: str = "./brain"
    logs_dir: str = "./logs"

    # Pipeline
    max_concurrent_jobs: int = 2
    max_retries: int = 3
    queue_db_path: str = "./pipeline/queue.db"

    # Scheduling
    uploads_per_day: int = 10
    schedule_start_hour: int = 7
    schedule_end_hour: int = 22

    # Logging
    log_level: str = "INFO"

    @property
    def brain_path(self) -> Path:
        return Path(self.brain_dir)

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)

    @property
    def assets_path(self) -> Path:
        return Path(self.assets_dir)


settings = Settings()
