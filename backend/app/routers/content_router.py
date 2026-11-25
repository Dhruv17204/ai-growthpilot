from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_authenticated_user
from app.models.models import ContentItem, BusinessProfile
from app.schemas.schemas import (
    ContentItemResponse, ContentItemCreate, ContentItemUpdate, GenerateContentPlanRequest
)
from app.services.content_service import generate_content_plan

router = APIRouter(tags=["Content Calendar"], dependencies=[Depends(require_authenticated_user)])

@router.post("/ai/content-plan")
async def create_content_plan(payload: GenerateContentPlanRequest, db: Session = Depends(get_db)):
    profile = db.query(BusinessProfile).first()
    items, meta = await generate_content_plan(
        db,
        payload.dict(),
        profile,
        force_demo_mode=payload.force_demo_mode
    )
    return {
        "items": items,
        "metadata": meta
    }

@router.get("/content", response_model=List[ContentItemResponse])
def list_content(db: Session = Depends(get_db)):
    return db.query(ContentItem).order_by(ContentItem.publication_date.asc()).all()

@router.post("/content", response_model=ContentItemResponse)
def create_content_item(payload: ContentItemCreate, db: Session = Depends(get_db)):
    item = ContentItem(
        title=payload.title,
        channel=payload.channel,
        publication_date=payload.publication_date,
        status=payload.status,
        content_text=payload.content_text,
        target_audience=payload.target_audience,
        tags=payload.tags,
        campaign_id=payload.campaign_id,
        is_demo=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/content/{item_id}", response_model=ContentItemResponse)
def update_content_item(item_id: int, payload: ContentItemUpdate, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    update_data = payload.dict(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(item, field, val)

    db.commit()
    db.refresh(item)
    return item

@router.delete("/content/{item_id}")
def delete_content_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    db.delete(item)
    db.commit()
    return {"message": "Content item deleted successfully"}
