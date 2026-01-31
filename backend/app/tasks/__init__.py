from app.tasks.celery_app import celery_app
from app.tasks.crawl_tasks import execute_crawl_task

__all__ = ["celery_app", "execute_crawl_task"]
