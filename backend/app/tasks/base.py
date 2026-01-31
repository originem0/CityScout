"""Base task classes for crawlers."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import CrawlTask

logger = logging.getLogger(__name__)


class BaseCrawlTask(Task, ABC):
    """Base class for all crawler tasks."""

    abstract = True

    def get_db_session_factory(self):
        """Create a new database session factory for each call."""
        engine = create_async_engine(settings.DATABASE_URL)
        return sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def update_task_status(
        self,
        task_id: UUID,
        status: str | None = None,
        progress: int | None = None,
        records_count: int | None = None,
        error_message: str | None = None,
    ):
        """Update task status in database."""
        session_factory = self.get_db_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(CrawlTask).where(CrawlTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                logger.warning(f"Task {task_id} not found")
                return

            if status:
                task.status = status
                if status == "running":
                    task.started_at = datetime.now()
                elif status in ["success", "failed", "cancelled"]:
                    task.finished_at = datetime.now()

            if progress is not None:
                task.progress = progress
            if records_count is not None:
                task.records_count = records_count
            if error_message is not None:
                task.error_message = error_message

            await db.commit()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        import asyncio

        crawl_task_id = kwargs.get("task_id") or (args[0] if args else None)
        if crawl_task_id:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    self.update_task_status(
                        UUID(crawl_task_id),
                        status="failed",
                        error_message=str(exc),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to update task status on failure: {e}")
            finally:
                loop.close()

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        # Status already updated in _run_crawl, skip to avoid event loop issues
        pass
