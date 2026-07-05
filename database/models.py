import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    Enum as SAEnum, JSON, BigInteger, Boolean, Time, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum


class Base(DeclarativeBase):
    pass


def ulid() -> str:
    return str(uuid.uuid4())


# ── Enums ──

class TopicStatus(str, enum.Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    READY = "ready"
    USED = "used"
    DROPPED = "dropped"


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    VOICING = "voicing"
    ASSEMBLING = "assembling"
    RENDERING = "rendering"
    THUMBNAILING = "thumbnailing"
    READY = "ready"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"


class QueueStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ── Tables ──

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    niche: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[TopicStatus] = mapped_column(
        SAEnum(TopicStatus), default=TopicStatus.PENDING
    )
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    scripts: Mapped[list["Script"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    topic_id: Mapped[str] = mapped_column(
        String, ForeignKey("topics.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hook_type: Mapped[str] = mapped_column(String(50), nullable=True)
    hook_text: Mapped[str] = mapped_column(String(500), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    tone: Mapped[str] = mapped_column(String(50), default="informative")
    language: Mapped[str] = mapped_column(String(10), default="id")
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    topic: Mapped[Topic] = relationship(back_populates="scripts")
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )
    voiceover: Mapped["VoiceOver | None"] = relationship(
        back_populates="script", uselist=False, cascade="all, delete-orphan"
    )
    video: Mapped["Video | None"] = relationship(
        back_populates="script", uselist=False, cascade="all, delete-orphan"
    )


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    script_id: Mapped[str] = mapped_column(
        String, ForeignKey("scripts.id"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    narration_text: Mapped[str] = mapped_column(Text, nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), default="stock_video")
    asset_query: Mapped[str] = mapped_column(String(500), nullable=True)
    asset_path: Mapped[str] = mapped_column(String(500), nullable=True)
    duration: Mapped[float] = mapped_column(Float, default=5.0)
    transition: Mapped[str] = mapped_column(String(50), default="fade")
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    script: Mapped[Script] = relationship(back_populates="scenes")


class VoiceOver(Base):
    __tablename__ = "voices"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    script_id: Mapped[str] = mapped_column(
        String, ForeignKey("scripts.id"), nullable=False, unique=True
    )
    voice_id: Mapped[str] = mapped_column(String(100), nullable=False)
    voice_name: Mapped[str] = mapped_column(String(100), nullable=True)
    audio_path: Mapped[str] = mapped_column(String(500), nullable=True)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    provider: Mapped[str] = mapped_column(String(50), default="edge")
    language: Mapped[str] = mapped_column(String(10), default="id")
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    script: Mapped[Script] = relationship(back_populates="voiceover")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    script_id: Mapped[str] = mapped_column(
        String, ForeignKey("scripts.id"), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        SAEnum(VideoStatus), default=VideoStatus.PENDING
    )
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[str] = mapped_column(String(500), nullable=True)
    thumbnail_style: Mapped[str] = mapped_column(String(50), nullable=True)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080")
    fps: Mapped[int] = mapped_column(Integer, default=30)
    file_size_mb: Mapped[float] = mapped_column(Float, default=0.0)
    youtube_id: Mapped[str] = mapped_column(String(50), nullable=True)
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    script: Mapped[Script] = relationship(back_populates="video")
    thumbnails: Mapped[list["Thumbnail"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    analytics: Mapped[list["Analytics"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )


class Thumbnail(Base):
    __tablename__ = "thumbnails"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("videos.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    style: Mapped[str] = mapped_column(String(50), default="modern")
    color_scheme: Mapped[str] = mapped_column(String(50), nullable=True)
    text_overlay: Mapped[str] = mapped_column(String(200), nullable=True)
    performance_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    a_b_test: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    video: Mapped[Video] = relationship(back_populates="thumbnails")


class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("videos.id"), nullable=False
    )
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, default=0)
    comments: Mapped[int] = mapped_column(BigInteger, default=0)
    shares: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_retention: Mapped[float] = mapped_column(Float, default=0.0)
    avg_view_duration: Mapped[float] = mapped_column(Float, default=0.0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(BigInteger, default=0)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    video: Mapped[Video] = relationship(back_populates="analytics")

    __table_args__ = (
        Index("idx_analytics_video_date", "video_id", "collected_at"),
    )


class UploadQueue(Base):
    __tablename__ = "upload_queue"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("videos.id"), nullable=False
    )
    status: Mapped[QueueStatus] = mapped_column(
        SAEnum(QueueStatus), default=QueueStatus.PENDING
    )
    stage: Mapped[str] = mapped_column(String(50), default="pending")
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    level: Mapped[LogLevel] = mapped_column(SAEnum(LogLevel))
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_logs_level_created", "level", "created_at"),
    )
