"""Manual import schemas for data validation."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ImportDataType(str, Enum):
    """Supported data types for import."""
    job = "job"
    rent = "rent"
    forum = "forum"


class JobImportRow(BaseModel):
    """Schema for a single job import row."""
    title: str
    company: str | None = None
    district: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_raw: str | None = None
    experience: str | None = None
    education: str | None = None
    tags: str | None = None
    description: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None


class RentImportRow(BaseModel):
    """Schema for a single rent import row."""
    title: str
    property_type: str | None = None
    district: str | None = None
    neighborhood: str | None = None
    price: Decimal | None = None
    price_raw: str | None = None
    area: Decimal | None = None
    layout: str | None = None
    floor: str | None = None
    subway_info: str | None = None
    facilities: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None


class ForumImportRow(BaseModel):
    """Schema for a single forum post import row."""
    title: str | None = None
    content: str
    author: str | None = None
    topic: str | None = None
    likes: int = 0
    replies_count: int = 0
    source_url: str | None = None
    posted_at: datetime | None = None


class ImportRequest(BaseModel):
    """Request for importing data."""
    data_type: ImportDataType
    city_id: int
    data_source_id: int
    rows: list[dict]  # Will be validated based on data_type


class ImportPreviewResponse(BaseModel):
    """Response for import preview."""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[dict]  # List of {row: int, field: str, error: str}
    preview: list[dict]  # First 10 valid rows


class ImportResultResponse(BaseModel):
    """Response for import result."""
    success: bool
    imported_count: int
    skipped_count: int
    errors: list[dict]


class SearchGuideRequest(BaseModel):
    """Request for generating search guide."""
    city_ids: list[int] | None = None  # None = all enabled cities
    keyword_ids: list[int] | None = None  # None = all enabled keywords


class PlatformSearchGuide(BaseModel):
    """Search guide for a single platform."""
    platform: str
    platform_name: str
    description: str
    search_urls: list[dict]  # List of {city, keyword, url}
    tips: list[str]
