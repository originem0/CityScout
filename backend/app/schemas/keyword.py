from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class KeywordCategory(str, Enum):
    job_search = "job_search"
    job_exclude = "job_exclude"
    forum_topic = "forum_topic"


class KeywordPriority(str, Enum):
    core = "core"
    extended = "extended"


class KeywordBase(BaseModel):
    category: KeywordCategory
    keyword: str
    priority: KeywordPriority = KeywordPriority.extended
    enabled: bool = True


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    category: KeywordCategory | None = None
    keyword: str | None = None
    priority: KeywordPriority | None = None
    enabled: bool | None = None


class KeywordResponse(KeywordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
