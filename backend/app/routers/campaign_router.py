from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_authenticated_user, require_admin_user
from app.models.models import Campaign, CampaignMetric
from app.schemas.schemas import CampaignResponse, GenerateCampaignRequest, CampaignUpdate
from app.services.campaign_service import generate_campaign

router = APIRouter(tags=["Campaign Studio"], dependencies=[Depends(require_authenticated_user)])

class CampaignGenerationOutput(BaseModel):
    campaign: CampaignResponse
    metadata: Dict[str, Any]

@router.post("/ai/campaign", response_model=CampaignGenerationOutput)
async def create_ai_campaign(payload: GenerateCampaignRequest, db: Session = Depends(get_db)):
    campaign, meta = await generate_campaign(
        db,
        payload.model_dump(),
        force_demo_mode=payload.force_demo_mode
    )
    return {
        "campaign": campaign,
        "metadata": meta
    }

@router.get("/campaigns", response_model=List[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()

@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c

@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: int, payload: CampaignUpdate, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(c, field, val)

    db.commit()
    db.refresh(c)
    return c

@router.delete("/campaigns/{campaign_id}", dependencies=[Depends(require_admin_user)])
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    # Convert associated campaign metrics to channel-level metrics before deletion
    db.query(CampaignMetric).filter(CampaignMetric.campaign_id == campaign_id).update({"campaign_id": None})
    db.delete(c)
    db.commit()
    return {"message": "Campaign deleted successfully"}
