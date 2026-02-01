"""Base task classes for crawlers."""
import asyncio
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
        current_state: str | None = None,
        current_page: int | None = None,
        total_pages: int | None = None,
        items_found: int | None = None,
        items_failed: int | None = None,
        error_type: str | None = None,
    ):
        """Update task status in database and publish to Redis."""
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
            if current_state is not None:
                task.current_state = current_state
            if current_page is not None:
                task.current_page = current_page
            if total_pages is not None:
                task.total_pages = total_pages
            if items_found is not None:
                task.items_found = items_found
            if items_failed is not None:
                task.items_failed = items_failed
            if error_type is not None:
                task.error_type = error_type

            await db.commit()

            # Publish progress to Redis for WebSocket clients
            try:
                from app.services.progress_publisher import get_publisher
                publisher = await get_publisher()
                await publisher.publish(str(task_id), {
                    "status": status or task.status,
                    "progress": progress if progress is not None else task.progress,
                    "records_count": records_count if records_count is not None else task.records_count,
                    "current_state": current_state or task.current_state,
                    "current_page": current_page if current_page is not None else task.current_page,
                    "total_pages": total_pages if total_pages is not None else task.total_pages,
                    "items_found": items_found if items_found is not None else task.items_found,
                    "items_failed": items_failed if items_failed is not None else task.items_failed,
                    "error_message": error_message,
                    "error_type": error_type,
                    "completed": status in ["success", "failed", "cancelled"] if status else False,
                })
            except Exception as e:
                logger.warning(f"Failed to publish progress to Redis: {e}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
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
