from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class DataSourceType(str, Enum):
    job = "job"
    rent = "rent"
    forum = "forum"
    public_data = "public_data"
    company_review = "company_review"
    salary_stats = "salary_stats"


class DataSourceBase(BaseModel):
    name: str
    type: DataSourceType
    slug: str
    enabled: bool = True
    priority: int = 10
    config: dict[str, Any] = {}


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: str | None = None
    type: DataSourceType | None = None
    slug: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    config: dict[str, Any] | None = None


class DataSourceResponse(DataSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_success_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
