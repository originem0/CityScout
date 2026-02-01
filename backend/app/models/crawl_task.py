import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # job_crawl / rent_crawl / forum_crawl / public_data
    data_source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("data_sources.id"), nullable=True
    )
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=True
    )
    keyword_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("keywords.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending / running / success / failed / cancelled
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 新增字段：细粒度进度跟踪
    current_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="init"
    )  # init/connecting/loading/parsing/saving/paginating/completed/failed
    current_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # timeout/blocked/captcha/parse_error/network/rate_limit/db_error/unknown
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    data_source = relationship("DataSource", lazy="joined")
    city = relationship("City", lazy="joined")
    keyword = relationship("Keyword", lazy="joined")
