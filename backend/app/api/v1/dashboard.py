"""Dashboard API endpoints."""
from fastapi import APIRouter
from sqlalchemy import select, func

from app.api.deps import DbSession
from app.models import City, Keyword, DataSource, CrawlTask, Job, Rent, ForumPost

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def dashboard_overview(db: DbSession):
    """Get dashboard overview stats."""
    city_count = (await db.execute(
        select(func.count(City.id)).where(City.enabled == True)
    )).scalar() or 0

    keyword_count = (await db.execute(
        select(func.count(Keyword.id)).where(Keyword.enabled == True)
    )).scalar() or 0

    source_count = (await db.execute(
        select(func.count(DataSource.id)).where(DataSource.enabled == True)
    )).scalar() or 0

    job_count = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    rent_count = (await db.execute(select(func.count(Rent.id)))).scalar() or 0
    forum_count = (await db.execute(select(func.count(ForumPost.id)))).scalar() or 0

    # Task stats
    task_stats_q = select(
        CrawlTask.status,
        func.count(CrawlTask.id).label("count"),
    ).group_by(CrawlTask.status)
    task_result = await db.execute(task_stats_q)
    task_stats = {r.status: r.count for r in task_result.all()}

    # Recent tasks
    recent_tasks_q = (
        select(CrawlTask)
        .order_by(CrawlTask.created_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_tasks_q)
    recent_tasks = recent_result.scalars().all()

    return {
        "counts": {
            "cities": city_count,
            "keywords": keyword_count,
            "sources": source_count,
            "jobs": job_count,
            "rent": rent_count,
            "forum": forum_count,
            "total_data": job_count + rent_count + forum_count,
        },
        "task_stats": {
            "pending": task_stats.get("pending", 0),
            "running": task_stats.get("running", 0),
            "success": task_stats.get("success", 0),
            "failed": task_stats.get("failed", 0),
            "total": sum(task_stats.values()),
        },
        "recent_tasks": [
            {
                "id": str(t.id),
                "task_type": t.task_type,
                "status": t.status,
                "progress": t.progress,
                "records_count": t.records_count,
                "created_at": t.created_at.isoformat(),
                "error_message": t.error_message,
            }
            for t in recent_tasks
        ],
    }
