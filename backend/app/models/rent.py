"""Rent listing model for storing crawled rental data."""
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


class Rent(Base):
    """Model for rental listings from property websites."""

    __tablename__ = "rents"

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

    # Listing identification
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Original ID from source website
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Property details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 整租/合租/公寓

    # Location
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # 小区名
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subway_info: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # 地铁信息

    # Price - stored in yuan/month
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_raw: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Original price text
    payment_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 押一付三 etc.

    # Property specifications
    area: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )  # Square meters
    area_raw: Mapped[str | None] = mapped_column(String(30), nullable=True)

    layout: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # e.g., "2室1厅1卫"
    floor: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # e.g., "中层/共18层"
    orientation: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # e.g., "朝南"
    decoration: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # e.g., "精装修"

    # Additional info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    facilities: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Comma-separated facilities
    images: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Comma-separated image URLs

    # Contact
    agent_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    agent_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

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
        return f"<Rent {self.title} - {self.price}元/月>"
