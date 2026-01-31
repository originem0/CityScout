from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskType(str, Enum):
    job_crawl = "job_crawl"
    rent_crawl = "rent_crawl"
    forum_crawl = "forum_crawl"
    public_data = "public_data"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class CrawlTaskCreate(BaseModel):
    task_type: TaskType
    data_source_id: int | None = None
    city_id: int | None = None
    keyword_id: int | None = None


class CrawlTaskUpdate(BaseModel):
    status: TaskStatus | None = None
    progress: int | None = None
    records_count: int | None = None
    error_message: str | None = None


class CrawlTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_type: str
    data_source_id: int | None
    city_id: int | None
    keyword_id: int | None
    status: str
    progress: int
    records_count: int
    error_message: str | None
    celery_task_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    # Related data (optional, for list view)
    data_source_name: str | None = None
    city_name: str | None = None
    keyword_text: str | None = None


class CrawlTaskDetailResponse(CrawlTaskResponse):
    """Extended response with full related data."""
    pass


class BatchTaskCreate(BaseModel):
    """Create tasks for multiple cities at once."""
    task_type: TaskType
    data_source_id: int
    city_ids: list[int] | None = None  # None means all enabled cities
    keyword_id: int | None = None
