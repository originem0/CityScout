"""WebSocket endpoints for real-time task progress updates."""
import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models import CrawlTask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


async def _get_task_state(task_id: str) -> dict | None:
    """Get current task state from database."""
    # Validate UUID format first
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        logger.warning(f"Invalid task ID format: {task_id}")
        return None

    async with async_session() as db:
        try:
            result = await db.execute(
                select(CrawlTask).where(CrawlTask.id == task_uuid)
            )
            task = result.scalar_one_or_none()
            if not task:
                return None

            return {
                "type": "initial",
                "task_id": task_id,
                "data": {
                    "status": task.status,
                    "progress": task.progress,
                    "records_count": task.records_count,
                    "current_state": task.current_state,
                    "current_page": task.current_page,
                    "total_pages": task.total_pages,
                    "items_found": task.items_found,
                    "items_failed": task.items_failed,
                    "error_message": task.error_message,
                    "error_type": task.error_type,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get task state: {e}")
            return None


@router.websocket("/tasks/{task_id}/progress")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task progress updates.

    Subscribes to Redis Pub/Sub channel for the given task and forwards
    all progress updates to the connected client.
    """
    # Validate task_id format before accepting
    try:
        UUID(task_id)
    except ValueError:
        await websocket.close(code=4000)
        return

    await websocket.accept()
    logger.info(f"WebSocket connected for task {task_id}")

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    channel = f"task_progress:{task_id}"

    try:
        # IMPORTANT: Subscribe FIRST to avoid missing messages during initial state fetch
        await pubsub.subscribe(channel)
        logger.debug(f"Subscribed to {channel}")

        # Then get initial task state
        initial_state = await _get_task_state(task_id)
        if initial_state:
            await websocket.send_json(initial_state)
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Task not found",
            })
            await websocket.close(code=4004)
            return

        # Check if task is already completed
        if initial_state["data"]["status"] in ["success", "failed", "cancelled"]:
            await websocket.send_json({
                "type": "completed",
                "task_id": task_id,
                "data": initial_state["data"],
            })
            # Keep connection open briefly for client to process
            await asyncio.sleep(1)
            return

        # Listen for messages with timeout
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=30.0,  # Heartbeat timeout
                )

                if message is None:
                    # Send heartbeat to keep connection alive
                    await websocket.send_json({"type": "heartbeat"})
                    continue

                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)

                    # Close connection if task completed
                    if data.get("data", {}).get("completed"):
                        logger.info(f"Task {task_id} completed, closing WebSocket")
                        break

            except asyncio.TimeoutError:
                # Check if task still running
                current_state = await _get_task_state(task_id)
                if current_state and current_state["data"]["status"] in ["success", "failed", "cancelled"]:
                    await websocket.send_json({
                        "type": "completed",
                        "task_id": task_id,
                        "data": current_state["data"],
                    })
                    break
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error",  # Don't expose internal errors
            })
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()
        logger.debug(f"Cleaned up WebSocket resources for task {task_id}")
