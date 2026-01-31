"""System logs API endpoints."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload

from app.database import async_session
from app.models import CrawlTask

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs(
    level: Optional[str] = Query(None, description="Log level: info, warning, error"),
    task_type: Optional[str] = Query(None, description="Task type filter"),
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=100),
):
    """Get system logs from task execution history."""
    async with async_session() as session:
        # Base query
        query = select(CrawlTask).options(
            joinedload(CrawlTask.data_source),
            joinedload(CrawlTask.city),
        )

        # Time filter
        since = datetime.utcnow() - timedelta(days=days)
        query = query.where(CrawlTask.created_at >= since)

        # Level filter (based on status)
        if level == "error":
            query = query.where(CrawlTask.status == "failed")
        elif level == "warning":
            query = query.where(CrawlTask.status.in_(["cancelled", "failed"]))
        elif level == "info":
            query = query.where(CrawlTask.status.in_(["success", "running", "pending"]))

        # Task type filter
        if task_type:
            query = query.where(CrawlTask.task_type == task_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate and sort
        query = query.order_by(desc(CrawlTask.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(query)
        tasks = result.unique().scalars().all()

        # Format as logs
        logs = []
        for task in tasks:
            # Determine log level based on status
            if task.status == "failed":
                log_level = "error"
            elif task.status == "cancelled":
                log_level = "warning"
            else:
                log_level = "info"

            # Create log message
            source_name = task.data_source.name if task.data_source else "未知"
            city_name = task.city.name if task.city else "未知"

            if task.status == "pending":
                message = f"任务已创建: {task.task_type} - {source_name} - {city_name}"
            elif task.status == "running":
                message = f"任务执行中: {task.task_type} - {source_name} - {city_name} (进度: {task.progress}%)"
            elif task.status == "success":
                message = f"任务完成: {task.task_type} - {source_name} - {city_name} (采集 {task.records_count} 条)"
            elif task.status == "failed":
                message = f"任务失败: {task.task_type} - {source_name} - {city_name}"
                if task.error_message:
                    message += f" - {task.error_message[:200]}"
            elif task.status == "cancelled":
                message = f"任务取消: {task.task_type} - {source_name} - {city_name}"
            else:
                message = f"任务状态未知: {task.task_type} - {task.status}"

            logs.append({
                "id": str(task.id),
                "timestamp": (task.finished_at or task.started_at or task.created_at).isoformat(),
                "level": log_level,
                "category": task.task_type,
                "message": message,
                "details": {
                    "task_id": str(task.id),
                    "status": task.status,
                    "source": source_name,
                    "city": city_name,
                    "records": task.records_count,
                    "error": task.error_message,
                },
            })

        return {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


@router.get("/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=30),
):
    """Get log statistics."""
    async with async_session() as session:
        since = datetime.utcnow() - timedelta(days=days)

        # Count by status
        query = select(
            CrawlTask.status,
            func.count(CrawlTask.id).label("count")
        ).where(
            CrawlTask.created_at >= since
        ).group_by(CrawlTask.status)

        result = await session.execute(query)
        status_counts = {row.status: row.count for row in result}

        # Count by task type
        query = select(
            CrawlTask.task_type,
            func.count(CrawlTask.id).label("count")
        ).where(
            CrawlTask.created_at >= since
        ).group_by(CrawlTask.task_type)

        result = await session.execute(query)
        type_counts = {row.task_type: row.count for row in result}

        return {
            "period_days": days,
            "by_level": {
                "info": status_counts.get("pending", 0) + status_counts.get("running", 0) + status_counts.get("success", 0),
                "warning": status_counts.get("cancelled", 0),
                "error": status_counts.get("failed", 0),
            },
            "by_status": status_counts,
            "by_type": type_counts,
            "total": sum(status_counts.values()),
        }
