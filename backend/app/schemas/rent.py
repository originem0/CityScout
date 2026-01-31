"""Rent schemas for API requests/responses."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RentBase(BaseModel):
    """Base rent fields."""

    title: str
    property_type: str | None = None
    district: str | None = None
    neighborhood: str | None = None
    address: str | None = None
    subway_info: str | None = None
    price: Decimal | None = None
    price_raw: str | None = None
    payment_type: str | None = None
    area: Decimal | None = None
    area_raw: str | None = None
    layout: str | None = None
    floor: str | None = None
    orientation: str | None = None
    decoration: str | None = None
    description: str | None = None
    facilities: str | None = None


class RentCreate(RentBase):
    """Fields for creating a rent listing."""

    data_source_id: int
    city_id: int
    crawl_task_id: UUID | None = None
    source_id: str
    source_url: str | None = None
    images: str | None = None
    agent_name: str | None = None
    agent_phone: str | None = None
    posted_at: datetime | None = None


class RentResponse(RentBase):
    """Rent response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_source_id: int
    city_id: int
    crawl_task_id: UUID | None
    source_id: str
    source_url: str | None
    images: str | None
    agent_name: str | None
    agent_phone: str | None
    posted_at: datetime | None
    crawled_at: datetime

    # Related names for display
    data_source_name: str | None = None
    city_name: str | None = None


class RentListResponse(BaseModel):
    """Rent list response with related names."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    property_type: str | None
    district: str | None
    neighborhood: str | None
    price: Decimal | None
    price_raw: str | None
    area: Decimal | None
    layout: str | None
    subway_info: str | None
    posted_at: datetime | None
    crawled_at: datetime
    city_name: str | None = None
    data_source_name: str | None = None
