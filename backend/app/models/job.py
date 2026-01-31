"""Job listing model for storing crawled job data."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Job(Base):
    """Model for job listings from recruitment websites."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Source tracking
    data_source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_sources.id"), nullable=False
    )
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=False
    )
    crawl_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crawl_tasks.id"), nullable=True
    )

    # Job identification
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Original ID from source website
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Job details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=True)
    company_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Location
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Salary - stored in yuan/month
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_raw: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Original salary text

    # Requirements
    experience: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "3-5年"
    education: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "本科"

    # Job description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Comma-separated tags

    # Benefits/welfare
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
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

    def __repr__(self):
        return f"<Job {self.title} @ {self.company}>"
