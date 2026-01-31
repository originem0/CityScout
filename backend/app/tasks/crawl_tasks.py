"""Crawl task definitions."""
import asyncio
import logging
from uuid import UUID

from app.tasks.celery_app import celery_app
from app.tasks.base import BaseCrawlTask

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=BaseCrawlTask, name="crawl.execute")
def execute_crawl_task(self, task_id: str, task_type: str, config: dict):
    """Execute a crawl task.

    Args:
        task_id: UUID of the CrawlTask record
        task_type: Type of crawl (job_crawl, rent_crawl, forum_crawl, public_data)
        config: Task configuration (city_id, data_source_id, keyword_id, etc.)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            _run_crawl(self, UUID(task_id), task_type, config)
        )
    finally:
        # Properly shutdown all async generators and close connections
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()
        # Reset the event loop to None so next task creates a fresh one
        asyncio.set_event_loop(None)


async def _run_crawl(
    task: BaseCrawlTask,
    task_id: UUID,
    task_type: str,
    config: dict,
):
    """Async implementation of crawl task."""
    logger.info(f"Starting crawl task {task_id} of type {task_type}")

    # Update status to running
    await task.update_task_status(task_id, status="running", progress=0)

    try:
        # Import appropriate crawler based on task type
        if task_type == "job_crawl":
            from app.crawlers.job_crawler import JobCrawler
            crawler = JobCrawler(config)
        elif task_type == "rent_crawl":
            from app.crawlers.rent_crawler import RentCrawler
            crawler = RentCrawler(config)
        elif task_type == "forum_crawl":
            from app.crawlers.forum_crawler import ForumCrawler
            crawler = ForumCrawler(config)
        elif task_type == "public_data":
            from app.crawlers.public_data_crawler import PublicDataCrawler
            crawler = PublicDataCrawler(config)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        # Run crawler with progress callback
        async def on_progress(progress: int, records: int):
            await task.update_task_status(
                task_id, progress=progress, records_count=records
            )

        result = await crawler.run(on_progress=on_progress)

        # Update final status
        await task.update_task_status(
            task_id,
            status="success",
            progress=100,
            records_count=result.get("records_count", 0),
        )

        logger.info(f"Crawl task {task_id} completed successfully")
        return result

    except Exception as e:
        logger.exception(f"Crawl task {task_id} failed: {e}")
        await task.update_task_status(
            task_id,
            status="failed",
            error_message=str(e),
        )
        raise
