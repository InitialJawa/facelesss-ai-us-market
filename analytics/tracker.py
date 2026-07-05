from typing import Any
from loguru import logger


class AnalyticsTracker:
    def __init__(self, brain):
        self.brain = brain

    async def track_upload(self, video_data: dict[str, Any]) -> None:
        logger.info(f"Tracking upload: {video_data.get('title', 'unknown')}")
        video_memory = self.brain.memory.get("video_memory", {})
        video_memory["total_uploaded"] = video_memory.get("total_uploaded", 0) + 1
        self.brain.set("video_memory", "total_uploaded", video_memory["total_uploaded"])

    async def track_performance(
        self, video_id: str, analytics: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info(f"Tracking performance: {video_id}")
        observations = {}
        if analytics.get("avg_retention", 0) > 50:
            observations["avg_retention"] = analytics["avg_retention"]
        if analytics.get("views", 0) > 1000:
            observations["best_duration"] = analytics.get("duration", 30)
        if observations:
            self.brain.learn("topic_memory", observations)
        return observations

    async def generate_report(self) -> dict[str, Any]:
        return {
            "total_videos": self.brain.get("video_memory", "total_uploaded"),
            "avg_views": self.brain.get("video_memory", "avg_views"),
            "avg_retention": self.brain.get("video_memory", "avg_retention"),
            "best_hook": self.brain.get("topic_memory", "best_hook"),
            "best_voice": self.brain.get("topic_memory", "best_voice"),
        }
