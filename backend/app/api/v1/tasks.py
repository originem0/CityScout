from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models import CrawlTask, City, DataSource, Keyword
from app.schemas import (
    CrawlTaskCreate,
    CrawlTaskUpdate,
    CrawlTaskResponse,
    CrawlTaskDetailResponse,
    BatchTaskCreate,
    MessageResponse,
    TaskStatus,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_response(task: CrawlTask) -> CrawlTaskResponse:
    """Convert CrawlTask model to response with related names."""
    return CrawlTaskResponse(
        id=task.id,
        task_type=task.task_type,
        data_source_id=task.data_source_id,
        city_id=task.city_id,
        keyword_id=task.keyword_id,
        status=task.status,
        progress=task.progress,
        records_count=task.records_count,
        error_message=task.error_message,
        celery_task_id=task.celery_task_id,
        started_at=task.started_at,
        finished_at=task.finished_at,
        created_at=task.created_at,
        data_source_name=task.data_source.name if task.data_source else None,
        city_name=task.city.name if task.city else None,
        keyword_text=task.keyword.keyword if task.keyword else None,
    )


@router.get("", response_model=list[CrawlTaskResponse])
async def list_tasks(
    db: DbSession,
    status: str | None = None,
    task_type: str | None = None,
    city_id: int | None = None,
    data_source_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
):
    """List crawl tasks with optional filters."""
    query = select(CrawlTask).options(
        selectinload(CrawlTask.data_source),
        selectinload(CrawlTask.city),
        selectinload(CrawlTask.keyword),
    )

    if status:
        query = query.where(CrawlTask.status == status)
    if task_type:
        query = query.where(CrawlTask.task_type == task_type)
    if city_id:
        query = query.where(CrawlTask.city_id == city_id)
    if data_source_id:
        query = query.where(CrawlTask.data_source_id == data_source_id)

    query = query.order_by(CrawlTask.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return [_task_to_response(task) for task in tasks]


@router.post("", response_model=CrawlTaskResponse, status_code=201)
async def create_task(db: DbSession, task_in: CrawlTaskCreate):
    """Create a new crawl task."""
    # Validate references
    if task_in.data_source_id:
        result = await db.execute(
            select(DataSource).where(DataSource.id == task_in.data_source_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Data source not found")

    if task_in.city_id:
        result = await db.execute(select(City).where(City.id == task_in.city_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="City not found")

    if task_in.keyword_id:
        result = await db.execute(select(Keyword).where(Keyword.id == task_in.keyword_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Keyword not found")

    task = CrawlTask(
        task_type=task_in.task_type.value,
        data_source_id=task_in.data_source_id,
        city_id=task_in.city_id,
        keyword_id=task_in.keyword_id,
    )
    db.add(task)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id == task.id)
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    task = result.scalar_one()

    return _task_to_response(task)


@router.post("/batch", response_model=list[CrawlTaskResponse], status_code=201)
async def create_batch_tasks(db: DbSession, batch_in: BatchTaskCreate):
    """Create tasks for multiple cities at once."""
    # Validate data source
    result = await db.execute(
        select(DataSource).where(DataSource.id == batch_in.data_source_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Data source not found")

    # Get city IDs
    if batch_in.city_ids:
        city_ids = batch_in.city_ids
    else:
        # Get all enabled cities
        result = await db.execute(select(City.id).where(City.enabled == True))
        city_ids = [row[0] for row in result.all()]

    if not city_ids:
        raise HTTPException(status_code=400, detail="No cities to create tasks for")

    # Validate keyword if provided
    if batch_in.keyword_id:
        result = await db.execute(
            select(Keyword).where(Keyword.id == batch_in.keyword_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Keyword not found")

    # Create tasks
    tasks = []
    for city_id in city_ids:
        task = CrawlTask(
            task_type=batch_in.task_type.value,
            data_source_id=batch_in.data_source_id,
            city_id=city_id,
            keyword_id=batch_in.keyword_id,
        )
        db.add(task)
        tasks.append(task)

    await db.commit()

    # Reload all tasks with relationships
    task_ids = [t.id for t in tasks]
    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id.in_(task_ids))
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    tasks = result.scalars().all()

    return [_task_to_response(task) for task in tasks]


@router.get("/{task_id}", response_model=CrawlTaskDetailResponse)
async def get_task(db: DbSession, task_id: UUID):
    """Get task details."""
    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id == task_id)
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@router.put("/{task_id}", response_model=CrawlTaskResponse)
async def update_task(db: DbSession, task_id: UUID, task_in: CrawlTaskUpdate):
    """Update task status/progress."""
    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id == task_id)
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.model_dump(exclude_unset=True)

    # Convert enum to string if present
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value

        # Set timestamps based on status
        if update_data["status"] == TaskStatus.running.value:
            update_data["started_at"] = datetime.now()
        elif update_data["status"] in [
            TaskStatus.success.value,
            TaskStatus.failed.value,
            TaskStatus.cancelled.value,
        ]:
            update_data["finished_at"] = datetime.now()

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return _task_to_response(task)


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(db: DbSession, task_id: UUID):
    """Delete a task."""
    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Only allow deleting pending or failed tasks
    if task.status not in ["pending", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running or completed tasks"
        )

    await db.delete(task)
    await db.commit()
    return MessageResponse(message="Task deleted")


@router.post("/{task_id}/cancel", response_model=CrawlTaskResponse)
async def cancel_task(db: DbSession, task_id: UUID):
    """Cancel a pending or running task."""
    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id == task_id)
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail="Can only cancel pending or running tasks"
        )

    task.status = TaskStatus.cancelled.value
    task.finished_at = datetime.now()

    # TODO: If running, also revoke the Celery task
    # if task.celery_task_id:
    #     celery_app.control.revoke(task.celery_task_id, terminate=True)

    await db.commit()
    await db.refresh(task)

    return _task_to_response(task)


@router.post("/{task_id}/start", response_model=CrawlTaskResponse)
async def start_task(db: DbSession, task_id: UUID):
    """Start executing a pending task."""
    from app.tasks.crawl_tasks import execute_crawl_task

    result = await db.execute(
        select(CrawlTask)
        .where(CrawlTask.id == task_id)
        .options(
            selectinload(CrawlTask.data_source),
            selectinload(CrawlTask.city),
            selectinload(CrawlTask.keyword),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Can only start pending tasks"
        )

    # Build config for crawler
    config = {
        "city_id": task.city_id,
        "data_source_id": task.data_source_id,
        "keyword_id": task.keyword_id,
    }

    # Send task to Celery
    celery_result = execute_crawl_task.delay(
        task_id=str(task.id),
        task_type=task.task_type,
        config=config,
    )

    # Store Celery task ID
    task.celery_task_id = celery_result.id
    task.status = "running"
    task.started_at = datetime.now()

    await db.commit()
    await db.refresh(task)

    return _task_to_response(task)


@router.get("/stats/summary")
async def get_task_stats(db: DbSession):
    """Get task statistics summary."""
    # Count by status
    result = await db.execute(
        select(CrawlTask.status, func.count(CrawlTask.id))
        .group_by(CrawlTask.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}

    # Total records collected
    result = await db.execute(select(func.sum(CrawlTask.records_count)))
    total_records = result.scalar() or 0

    return {
        "pending": status_counts.get("pending", 0),
        "running": status_counts.get("running", 0),
        "success": status_counts.get("success", 0),
        "failed": status_counts.get("failed", 0),
        "cancelled": status_counts.get("cancelled", 0),
        "total_records": total_records,
    }
