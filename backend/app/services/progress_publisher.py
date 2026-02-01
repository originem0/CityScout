"""Redis Pub/Sub service for real-time task progress updates."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class ProgressPublisher:
    """Publishes task progress updates via Redis Pub/Sub."""

    CHANNEL_PREFIX = "task_progress:"

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self):
        """Connect to Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("ProgressPublisher connected to Redis")

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("ProgressPublisher disconnected from Redis")

    async def publish(self, task_id: str, progress: dict[str, Any]) -> int:
        """Publish progress update to Redis channel.

        Args:
            task_id: The crawl task ID
            progress: Progress data dict containing status, progress%, etc.

        Returns:
            Number of subscribers that received the message
        """
        if not self._redis:
            await self.connect()

        channel = f"{self.CHANNEL_PREFIX}{task_id}"
        message = json.dumps({
            "type": "progress",
            "task_id": task_id,
            "data": progress,
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)

        try:
            subscribers = await self._redis.publish(channel, message)
            logger.debug(f"Published progress to {channel}: {subscribers} subscribers")
            return subscribers
        except Exception as e:
            logger.error(f"Failed to publish progress for task {task_id}: {e}")
            return 0

    async def publish_completion(self, task_id: str, status: str, records_count: int = 0):
        """Publish task completion event.

        Args:
            task_id: The crawl task ID
            status: Final status (success/failed/cancelled)
            records_count: Total records collected
        """
        await self.publish(task_id, {
            "status": status,
            "progress": 100 if status == "success" else None,
            "records_count": records_count,
            "completed": True,
        })


# Global publisher instance with lock for thread-safe initialization
_publisher: ProgressPublisher | None = None
_publisher_lock = asyncio.Lock()


async def get_publisher() -> ProgressPublisher:
    """Get or create the global ProgressPublisher instance.

    Thread-safe initialization using asyncio.Lock to prevent race conditions.
    """
    global _publisher
    async with _publisher_lock:
        if _publisher is None:
            _publisher = ProgressPublisher()
            await _publisher.connect()
    return _publisher


async def close_publisher():
    """Close the global publisher connection."""
    global _publisher
    async with _publisher_lock:
        if _publisher:
            await _publisher.close()
            _publisher = None
