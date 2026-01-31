from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import DataSource
from app.schemas import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    MessageResponse,
)

router = APIRouter(prefix="/sources", tags=["data sources"])


@router.get("", response_model=list[DataSourceResponse])
async def list_sources(
    db: DbSession,
    type: str | None = None,
    enabled: bool | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(DataSource)
    if type:
        query = query.where(DataSource.type == type)
    if enabled is not None:
        query = query.where(DataSource.enabled == enabled)
    query = query.order_by(DataSource.priority, DataSource.id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=DataSourceResponse, status_code=201)
async def create_source(db: DbSession, source_in: DataSourceCreate):
    existing = await db.execute(
        select(DataSource).where(DataSource.slug == source_in.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Data source slug already exists")

    source = DataSource(**source_in.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_source(db: DbSession, source_id: int):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.put("/{source_id}", response_model=DataSourceResponse)
async def update_source(db: DbSession, source_id: int, source_in: DataSourceUpdate):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    update_data = source_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", response_model=MessageResponse)
async def delete_source(db: DbSession, source_id: int):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    await db.delete(source)
    await db.commit()
    return MessageResponse(message="Data source deleted")


@router.patch("/{source_id}/toggle", response_model=DataSourceResponse)
async def toggle_source(db: DbSession, source_id: int):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    source.enabled = not source.enabled
    await db.commit()
    await db.refresh(source)
    return source
