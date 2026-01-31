from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class CityTier(str, Enum):
    tier1 = "tier1"
    new_tier1 = "new_tier1"
    tier2 = "tier2"
    tier3 = "tier3"


class CityBase(BaseModel):
    name: str
    province: str
    tier: CityTier = CityTier.tier2
    enabled: bool = True


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: str | None = None
    province: str | None = None
    tier: CityTier | None = None
    enabled: bool | None = None


class CityResponse(CityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
