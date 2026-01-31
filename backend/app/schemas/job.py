"""Job schemas for API requests/responses."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobBase(BaseModel):
    """Base job fields."""

    title: str
    company: str | None = None
    company_type: str | None = None
    company_size: str | None = None
    district: str | None = None
    address: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_raw: str | None = None
    experience: str | None = None
    education: str | None = None
    description: str | None = None
    tags: str | None = None
    benefits: str | None = None


class JobCreate(JobBase):
    """Fields for creating a job."""

    data_source_id: int
    city_id: int
    crawl_task_id: UUID | None = None
    source_id: str
    source_url: str | None = None
    posted_at: datetime | None = None


class JobResponse(JobBase):
    """Job response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_source_id: int
    city_id: int
    crawl_task_id: UUID | None
    source_id: str
    source_url: str | None
    posted_at: datetime | None
    crawled_at: datetime

    # Related names for display
    data_source_name: str | None = None
    city_name: str | None = None


class JobListResponse(BaseModel):
    """Job list response with related names."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str | None
    district: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_raw: str | None
    experience: str | None
    education: str | None
    tags: str | None
    posted_at: datetime | None
    crawled_at: datetime
    city_name: str | None = None
    data_source_name: str | None = None
