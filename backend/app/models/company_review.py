"""Company review model for storing company ratings and salary statistics."""
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


class CompanyReview(Base):
    """Model for company reviews and salary statistics from various sources."""

    __tablename__ = "company_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Company identification (unique for upsert operations)
    company_name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )

    # Source tracking
    data_source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_sources.id"), nullable=False
    )

    # 看准网评分字段 (1-5 scale, 3.2 precision)
    overall_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    culture_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    management_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    salary_benefit_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    career_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    work_life_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )

    # Statistics
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommend_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True  # e.g., 85.50%
    )

    # 职友集薪资分位数字段
    salary_p25: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    salary_p50: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    salary_p75: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    salary_sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    company_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    match_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True  # 0.00-1.00
    )
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    data_source = relationship("DataSource", lazy="joined")

    def __repr__(self):
        return f"<CompanyReview {self.company_name} @ {self.data_source.name if self.data_source else 'N/A'}>"
