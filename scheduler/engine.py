import asyncio
from datetime import datetime, time
from typing import Any, Callable
from loguru import logger


class ScheduleEngine:
    def __init__(self):
        self._jobs: list[dict[str, Any]] = []
        self._running = False

    def add_daily(
        self,
        name: str,
        callback: Callable,
        hour: int,
        minute: int = 0,
    ) -> None:
        self._jobs.append({
            "name": name,
            "callback": callback,
            "hour": hour,
            "minute": minute,
            "type": "daily",
            "last_run": None,
        })
        logger.info(f"Schedule: '{name}' daily at {hour:02d}:{minute:02d}")

    def add_interval(
        self,
        name: str,
        callback: Callable,
        interval_minutes: int,
    ) -> None:
        self._jobs.append({
            "name": name,
            "callback": callback,
            "interval": interval_minutes,
            "type": "interval",
            "last_run": None,
        })
        logger.info(f"Schedule: '{name}' every {interval_minutes}min")

    async def tick(self) -> list[str]:
        now = datetime.now()
        triggered = []
        for job in self._jobs:
            should_run = False
            if job["type"] == "daily":
                target = now.replace(
                    hour=job["hour"], minute=job["minute"], second=0, microsecond=0
                )
                if now >= target and (
                    job["last_run"] is None or job["last_run"] < target
                ):
                    should_run = True
            elif job["type"] == "interval":
                if job["last_run"] is None:
                    should_run = True
                else:
                    elapsed = (now - job["last_run"]).total_seconds() / 60
                    if elapsed >= job["interval"]:
                        should_run = True
            if should_run:
                try:
                    if asyncio.iscoroutinefunction(job["callback"]):
                        await job["callback"]()
                    else:
                        job["callback"]()
                    job["last_run"] = now
                    triggered.append(job["name"])
                    logger.info(f"Schedule triggered: {job['name']}")
                except Exception as e:
                    logger.error(f"Schedule failed '{job['name']}': {e}")
        return triggered

    async def run_loop(self, tick_interval: int = 30):
        self._running = True
        logger.info("Schedule engine started")
        while self._running:
            await self.tick()
            await asyncio.sleep(tick_interval)

    def stop(self):
        self._running = False
        logger.info("Schedule engine stopped")

