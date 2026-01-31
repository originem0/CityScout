"""Jobs data browsing API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.models import Job, City, DataSource
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobListResponse])
async def list_jobs(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city_id: int | None = None,
    data_source_id: int | None = None,
    search: str | None = None,
    district: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    sort_by: str = "crawled_at",
    sort_order: str = "desc",
):
    """List jobs with filters and pagination."""
    # Base query
    query = select(Job).options(
        joinedload(Job.city),
        joinedload(Job.data_source),
    )

    # Apply filters
    if city_id:
        query = query.where(Job.city_id == city_id)
    if data_source_id:
        query = query.where(Job.data_source_id == data_source_id)
    if district:
        query = query.where(Job.district.ilike(f"%{district}%"))
    if salary_min:
        query = query.where(Job.salary_min >= salary_min)
    if salary_max:
        query = query.where(Job.salary_max <= salary_max)
    if search:
        query = query.where(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply sorting
    sort_column = getattr(Job, sort_by, Job.crawled_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().unique().all()

    # Convert to response format with related names
    items = []
    for job in jobs:
        item = JobListResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            district=job.district,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_raw=job.salary_raw,
            experience=job.experience,
            education=job.education,
            tags=job.tags,
            posted_at=job.posted_at,
            crawled_at=job.crawled_at,
            city_name=job.city.name if job.city else None,
            data_source_name=job.data_source.name if job.data_source else None,
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    db: DbSession,
    job_id: UUID,
):
    """Get a single job by ID."""
    query = select(Job).options(
        joinedload(Job.city),
        joinedload(Job.data_source),
    ).where(Job.id == job_id)

    result = await db.execute(query)
    job = result.scalars().first()

    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        company_type=job.company_type,
        company_size=job.company_size,
        district=job.district,
        address=job.address,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_raw=job.salary_raw,
        experience=job.experience,
        education=job.education,
        description=job.description,
        tags=job.tags,
        benefits=job.benefits,
        data_source_id=job.data_source_id,
        city_id=job.city_id,
        crawl_task_id=job.crawl_task_id,
        source_id=job.source_id,
        source_url=job.source_url,
        posted_at=job.posted_at,
        crawled_at=job.crawled_at,
        city_name=job.city.name if job.city else None,
        data_source_name=job.data_source.name if job.data_source else None,
    )


@router.get("/stats/summary")
async def get_jobs_stats(
    db: DbSession,
    city_id: int | None = None,
):
    """Get job statistics."""
    query = select(
        func.count(Job.id).label("total"),
        func.avg(Job.salary_min).label("avg_salary_min"),
        func.avg(Job.salary_max).label("avg_salary_max"),
        func.min(Job.salary_min).label("min_salary"),
        func.max(Job.salary_max).label("max_salary"),
    )

    if city_id:
        query = query.where(Job.city_id == city_id)

    result = await db.execute(query)
    row = result.first()

    return {
        "total": row.total or 0,
        "avg_salary_min": float(row.avg_salary_min) if row.avg_salary_min else None,
        "avg_salary_max": float(row.avg_salary_max) if row.avg_salary_max else None,
        "min_salary": float(row.min_salary) if row.min_salary else None,
        "max_salary": float(row.max_salary) if row.max_salary else None,
    }
