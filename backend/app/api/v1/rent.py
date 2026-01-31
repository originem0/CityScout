"""Rent data browsing API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.models import Rent, City, DataSource
from app.schemas.rent import RentResponse, RentListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/rent", tags=["rent"])


@router.get("", response_model=PaginatedResponse[RentListResponse])
async def list_rent(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city_id: int | None = None,
    data_source_id: int | None = None,
    search: str | None = None,
    district: str | None = None,
    property_type: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    area_min: int | None = None,
    area_max: int | None = None,
    sort_by: str = "crawled_at",
    sort_order: str = "desc",
):
    """List rent listings with filters and pagination."""
    # Base query
    query = select(Rent).options(
        joinedload(Rent.city),
        joinedload(Rent.data_source),
    )

    # Apply filters
    if city_id:
        query = query.where(Rent.city_id == city_id)
    if data_source_id:
        query = query.where(Rent.data_source_id == data_source_id)
    if district:
        query = query.where(Rent.district.ilike(f"%{district}%"))
    if property_type:
        query = query.where(Rent.property_type == property_type)
    if price_min:
        query = query.where(Rent.price >= price_min)
    if price_max:
        query = query.where(Rent.price <= price_max)
    if area_min:
        query = query.where(Rent.area >= area_min)
    if area_max:
        query = query.where(Rent.area <= area_max)
    if search:
        query = query.where(
            or_(
                Rent.title.ilike(f"%{search}%"),
                Rent.neighborhood.ilike(f"%{search}%"),
                Rent.description.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply sorting
    sort_column = getattr(Rent, sort_by, Rent.crawled_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    rents = result.scalars().unique().all()

    # Convert to response format with related names
    items = []
    for rent in rents:
        item = RentListResponse(
            id=rent.id,
            title=rent.title,
            property_type=rent.property_type,
            district=rent.district,
            neighborhood=rent.neighborhood,
            price=rent.price,
            price_raw=rent.price_raw,
            area=rent.area,
            layout=rent.layout,
            subway_info=rent.subway_info,
            posted_at=rent.posted_at,
            crawled_at=rent.crawled_at,
            city_name=rent.city.name if rent.city else None,
            data_source_name=rent.data_source.name if rent.data_source else None,
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{rent_id}", response_model=RentResponse)
async def get_rent(
    db: DbSession,
    rent_id: UUID,
):
    """Get a single rent listing by ID."""
    query = select(Rent).options(
        joinedload(Rent.city),
        joinedload(Rent.data_source),
    ).where(Rent.id == rent_id)

    result = await db.execute(query)
    rent = result.scalars().first()

    if not rent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Rent listing not found")

    return RentResponse(
        id=rent.id,
        title=rent.title,
        property_type=rent.property_type,
        district=rent.district,
        neighborhood=rent.neighborhood,
        address=rent.address,
        subway_info=rent.subway_info,
        price=rent.price,
        price_raw=rent.price_raw,
        payment_type=rent.payment_type,
        area=rent.area,
        area_raw=rent.area_raw,
        layout=rent.layout,
        floor=rent.floor,
        orientation=rent.orientation,
        decoration=rent.decoration,
        description=rent.description,
        facilities=rent.facilities,
        data_source_id=rent.data_source_id,
        city_id=rent.city_id,
        crawl_task_id=rent.crawl_task_id,
        source_id=rent.source_id,
        source_url=rent.source_url,
        images=rent.images,
        agent_name=rent.agent_name,
        agent_phone=rent.agent_phone,
        posted_at=rent.posted_at,
        crawled_at=rent.crawled_at,
        city_name=rent.city.name if rent.city else None,
        data_source_name=rent.data_source.name if rent.data_source else None,
    )


@router.get("/stats/summary")
async def get_rent_stats(
    db: DbSession,
    city_id: int | None = None,
):
    """Get rent statistics."""
    query = select(
        func.count(Rent.id).label("total"),
        func.avg(Rent.price).label("avg_price"),
        func.min(Rent.price).label("min_price"),
        func.max(Rent.price).label("max_price"),
        func.avg(Rent.area).label("avg_area"),
    )

    if city_id:
        query = query.where(Rent.city_id == city_id)

    result = await db.execute(query)
    row = result.first()

    return {
        "total": row.total or 0,
        "avg_price": float(row.avg_price) if row.avg_price else None,
        "min_price": float(row.min_price) if row.min_price else None,
        "max_price": float(row.max_price) if row.max_price else None,
        "avg_area": float(row.avg_area) if row.avg_area else None,
    }
