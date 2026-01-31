from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.api.deps import DbSession
from app.models import City
from app.schemas import CityCreate, CityUpdate, CityResponse, MessageResponse

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=list[CityResponse])
async def list_cities(
    db: DbSession,
    enabled: bool | None = None,
    tier: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(City)
    if enabled is not None:
        query = query.where(City.enabled == enabled)
    if tier:
        query = query.where(City.tier == tier)
    query = query.order_by(City.id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CityResponse, status_code=201)
async def create_city(db: DbSession, city_in: CityCreate):
    existing = await db.execute(select(City).where(City.name == city_in.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="City already exists")

    city = City(**city_in.model_dump())
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return city


@router.get("/{city_id}", response_model=CityResponse)
async def get_city(db: DbSession, city_id: int):
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city


@router.put("/{city_id}", response_model=CityResponse)
async def update_city(db: DbSession, city_id: int, city_in: CityUpdate):
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    update_data = city_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(city, field, value)

    await db.commit()
    await db.refresh(city)
    return city


@router.delete("/{city_id}", response_model=MessageResponse)
async def delete_city(db: DbSession, city_id: int):
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    await db.delete(city)
    await db.commit()
    return MessageResponse(message="City deleted")


@router.patch("/{city_id}/toggle", response_model=CityResponse)
async def toggle_city(db: DbSession, city_id: int):
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    city.enabled = not city.enabled
    await db.commit()
    await db.refresh(city)
    return city
