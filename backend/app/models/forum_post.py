"""Forum comment/post model for storing crawled forum data."""
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ForumPost(Base):
    """Model for forum posts and comments from various sources."""

    __tablename__ = "forum_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Source tracking
    data_source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_sources.id"), nullable=False
    )
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=True
    )
    crawl_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crawl_tasks.id"), nullable=True
    )

    # Post identification
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Original ID from source
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Post type
    post_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="post"
    )  # post / comment / reply

    # Parent post (for comments/replies)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True
    )

    # Content
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Author info
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    author_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    author_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Engagement metrics
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Topic/tags
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Forum/board name
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Comma-separated

    # Search context
    search_keyword: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # What keyword was used to find this

    # Sentiment (for later analysis)
    sentiment: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # positive / negative / neutral

    # Timestamps
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    data_source = relationship("DataSource", lazy="joined")
    city = relationship("City", lazy="joined")
    crawl_task = relationship("CrawlTask", lazy="select")
    parent = relationship("ForumPost", remote_side=[id], lazy="select")

    def __repr__(self):
        return f"<ForumPost {self.title or self.content[:30]}>"
