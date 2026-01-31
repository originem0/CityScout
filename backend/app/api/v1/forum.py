"""Forum posts data browsing API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.models import ForumPost, City, DataSource
from app.schemas.forum_post import ForumPostResponse, ForumPostListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/forum", tags=["forum"])


@router.get("", response_model=PaginatedResponse[ForumPostListResponse])
async def list_forum_posts(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city_id: int | None = None,
    data_source_id: int | None = None,
    search: str | None = None,
    topic: str | None = None,
    post_type: str | None = None,
    author: str | None = None,
    sort_by: str = "crawled_at",
    sort_order: str = "desc",
):
    """List forum posts with filters and pagination."""
    # Base query
    query = select(ForumPost).options(
        joinedload(ForumPost.city),
        joinedload(ForumPost.data_source),
    )

    # Apply filters
    if city_id:
        query = query.where(ForumPost.city_id == city_id)
    if data_source_id:
        query = query.where(ForumPost.data_source_id == data_source_id)
    if topic:
        query = query.where(ForumPost.topic.ilike(f"%{topic}%"))
    if post_type:
        query = query.where(ForumPost.post_type == post_type)
    if author:
        query = query.where(ForumPost.author.ilike(f"%{author}%"))
    if search:
        query = query.where(
            or_(
                ForumPost.title.ilike(f"%{search}%"),
                ForumPost.content.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply sorting
    sort_column = getattr(ForumPost, sort_by, ForumPost.crawled_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().unique().all()

    # Convert to response format with related names
    items = []
    for post in posts:
        item = ForumPostListResponse(
            id=post.id,
            title=post.title,
            content=post.content[:500] if post.content and len(post.content) > 500 else post.content,
            author=post.author,
            topic=post.topic,
            likes=post.likes,
            replies_count=post.replies_count,
            post_type=post.post_type,
            source_url=post.source_url,
            posted_at=post.posted_at,
            crawled_at=post.crawled_at,
            city_name=post.city.name if post.city else None,
            data_source_name=post.data_source.name if post.data_source else None,
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{post_id}", response_model=ForumPostResponse)
async def get_forum_post(
    db: DbSession,
    post_id: UUID,
):
    """Get a single forum post by ID."""
    query = select(ForumPost).options(
        joinedload(ForumPost.city),
        joinedload(ForumPost.data_source),
    ).where(ForumPost.id == post_id)

    result = await db.execute(query)
    post = result.scalars().first()

    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Forum post not found")

    return ForumPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        topic=post.topic,
        tags=post.tags,
        likes=post.likes,
        replies_count=post.replies_count,
        views=post.views,
        data_source_id=post.data_source_id,
        city_id=post.city_id,
        crawl_task_id=post.crawl_task_id,
        source_id=post.source_id,
        source_url=post.source_url,
        post_type=post.post_type,
        parent_id=post.parent_id,
        author_id=post.author_id,
        search_keyword=post.search_keyword,
        sentiment=post.sentiment,
        posted_at=post.posted_at,
        crawled_at=post.crawled_at,
        city_name=post.city.name if post.city else None,
        data_source_name=post.data_source.name if post.data_source else None,
    )


@router.get("/stats/summary")
async def get_forum_stats(
    db: DbSession,
    city_id: int | None = None,
):
    """Get forum post statistics."""
    query = select(
        func.count(ForumPost.id).label("total"),
        func.sum(ForumPost.likes).label("total_likes"),
        func.sum(ForumPost.replies_count).label("total_replies"),
        func.avg(ForumPost.likes).label("avg_likes"),
    )

    if city_id:
        query = query.where(ForumPost.city_id == city_id)

    result = await db.execute(query)
    row = result.first()

    # Count by post_type
    type_query = select(
        ForumPost.post_type,
        func.count(ForumPost.id).label("count"),
    ).group_by(ForumPost.post_type)

    if city_id:
        type_query = type_query.where(ForumPost.city_id == city_id)

    type_result = await db.execute(type_query)
    type_counts = {r.post_type: r.count for r in type_result.all()}

    return {
        "total": row.total or 0,
        "total_likes": row.total_likes or 0,
        "total_replies": row.total_replies or 0,
        "avg_likes": float(row.avg_likes) if row.avg_likes else None,
        "by_type": type_counts,
    }
