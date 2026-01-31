from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import Keyword
from app.schemas import KeywordCreate, KeywordUpdate, KeywordResponse, MessageResponse

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordResponse])
async def list_keywords(
    db: DbSession,
    category: str | None = None,
    enabled: bool | None = None,
    priority: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(Keyword)
    if category:
        query = query.where(Keyword.category == category)
    if enabled is not None:
        query = query.where(Keyword.enabled == enabled)
    if priority:
        query = query.where(Keyword.priority == priority)
    query = query.order_by(Keyword.id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(db: DbSession, keyword_in: KeywordCreate):
    existing = await db.execute(
        select(Keyword).where(
            Keyword.category == keyword_in.category,
            Keyword.keyword == keyword_in.keyword,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Keyword already exists in this category")

    keyword = Keyword(**keyword_in.model_dump())
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    return keyword


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(db: DbSession, keyword_id: int):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(db: DbSession, keyword_id: int, keyword_in: KeywordUpdate):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    update_data = keyword_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(keyword, field, value)

    await db.commit()
    await db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}", response_model=MessageResponse)
async def delete_keyword(db: DbSession, keyword_id: int):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await db.delete(keyword)
    await db.commit()
    return MessageResponse(message="Keyword deleted")
