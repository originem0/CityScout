"""Forum post schemas for API requests/responses."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ForumPostBase(BaseModel):
    """Base forum post fields."""

    title: str | None = None
    content: str
    author: str | None = None
    topic: str | None = None
    tags: str | None = None
    likes: int = 0
    replies_count: int = 0
    views: int = 0


class ForumPostCreate(ForumPostBase):
    """Fields for creating a forum post."""

    data_source_id: int
    city_id: int | None = None
    crawl_task_id: UUID | None = None
    source_id: str
    source_url: str | None = None
    post_type: str = "post"
    parent_id: UUID | None = None
    content_html: str | None = None
    author_id: str | None = None
    author_avatar: str | None = None
    search_keyword: str | None = None
    sentiment: str | None = None
    posted_at: datetime | None = None


class ForumPostResponse(ForumPostBase):
    """Forum post response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_source_id: int
    city_id: int | None
    crawl_task_id: UUID | None
    source_id: str
    source_url: str | None
    post_type: str
    parent_id: UUID | None
    author_id: str | None
    search_keyword: str | None
    sentiment: str | None
    posted_at: datetime | None
    crawled_at: datetime

    # Related names for display
    data_source_name: str | None = None
    city_name: str | None = None


class ForumPostListResponse(BaseModel):
    """Forum post list response with key fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    content: str
    author: str | None
    topic: str | None
    likes: int
    replies_count: int
    post_type: str
    source_url: str | None
    posted_at: datetime | None
    crawled_at: datetime
    city_name: str | None = None
    data_source_name: str | None = None
