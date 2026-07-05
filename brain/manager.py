from pathlib import Path
from typing import Any
from datetime import datetime
import json

from loguru import logger


DEFAULT_BRAIN = {
    "topic_memory": {
        "best_niches": [],
        "best_duration": 0,
        "best_hook": "",
        "best_voice": "",
        "best_topic": "",
        "avoid_words": [],
        "best_posting_time": "",
        "top_performing_topics": [],
        "underperforming_topics": [],
    },
    "video_memory": {
        "total_generated": 0,
        "total_uploaded": 0,
        "avg_views": 0,
        "avg_retention": 0,
        "best_performers": [],
    },
    "thumbnail_memory": {
        "best_styles": [],
        "best_colors": [],
        "worst_styles": [],
    },
    "performance": {
        "avg_render_time": 0,
        "avg_script_time": 0,
        "error_rate": 0,
        "last_24h_count": 0,
    },
    "style": {
        "narration_speed": 1.0,
        "subtitle_style": "default",
        "music_style": "cinematic",
        "transition_style": "fade",
        "background_color": "#1a1a2e",
    },
    "schedule": {
        "preferred_hours": [],
        "upload_times": ["07:00", "12:00", "18:00"],
    },
}


class Brain:
    def __init__(self, brain_dir: str | Path):
        self.brain_dir = Path(brain_dir)
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        self.memory: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> dict[str, Any]:
        self.memory = {}
        for key, default in DEFAULT_BRAIN.items():
            path = self.brain_dir / f"{key}.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    self.memory[key] = data
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Corrupt brain file {path.name}: {e}. Resetting.")
                    self.memory[key] = default.copy()
                    path.write_text(json.dumps(default, indent=2))
            else:
                self.memory[key] = default.copy()
                path.write_text(json.dumps(default, indent=2))
        self._loaded = True
        logger.info(f"Brain loaded: {len(self.memory)} modules")
        return self.memory

    def save(self) -> None:
        for key, data in self.memory.items():
            path = self.brain_dir / f"{key}.json"
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.debug("Brain saved to disk")

    def get(self, module: str, key: str | None = None) -> Any:
        if not self._loaded:
            self.load()
        module_data = self.memory.get(module, {})
        if key:
            return module_data.get(key)
        return module_data

    def set(self, module: str, key: str, value: Any) -> None:
        if not self._loaded:
            self.load()
        if module not in self.memory:
            self.memory[module] = {}
        self.memory[module][key] = value
        self.save()

    def learn(self, module: str, observation: dict[str, Any]) -> None:
        if not self._loaded:
            self.load()
        memory = self.memory.get(module, {})
        for key, value in observation.items():
            if key in memory:
                existing = memory[key]
                if isinstance(existing, list):
                    if isinstance(value, list):
                        memory[key] = value
                    else:
                        memory[key] = [value] + existing[:9]
                elif isinstance(existing, (int, float)):
                    alpha = 0.3
                    memory[key] = (1 - alpha) * existing + alpha * value
                else:
                    memory[key] = value

        self.memory[module] = memory
        self.save()
        logger.info(f"Brain learned: {module}.{list(observation.keys())}")

    def suggest_hook(self) -> str:
        hooks = self.get("topic_memory", "best_hook")
        if isinstance(hooks, str) and hooks:
            return hooks
        if isinstance(hooks, list) and hooks:
            return hooks[0]
        return "question"

    def suggest_voice(self) -> str:
        voice = self.get("topic_memory", "best_voice")
        return voice if voice else "id-ID-ArdiNeural"

    def suggest_duration(self) -> int:
        dur = self.get("topic_memory", "best_duration")
        return int(dur) if dur else 30

    def avoid_words(self) -> list[str]:
        words = self.get("topic_memory", "avoid_words")
        return words if isinstance(words, list) else ["actually", "basically"]

    def to_dict(self) -> dict[str, Any]:
        if not self._loaded:
            self.load()
        return self.memory

    @classmethod
    def init_defaults(cls, brain_dir: str | Path) -> "Brain":
        brain = cls(brain_dir)
        brain.load()
        return brain
