from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import GrowthStrategy, BusinessProfile
from app.schemas.schemas import (
    GrowthStrategyResponse, GenerateStrategyRequest, StrategySectionRegenerateRequest
)
from app.services.ai_strategy_service import generate_growth_strategy, generate_fallback_strategy

router = APIRouter(tags=["AI Strategy"])

class StrategyGenerationOutput(BaseModel):
    strategy: GrowthStrategyResponse
    metadata: Dict[str, Any]

@router.post("/ai/strategy", response_model=StrategyGenerationOutput)
async def create_strategy(payload: GenerateStrategyRequest, db: Session = Depends(get_db)):
    profile = None
    if payload.business_profile_id:
        profile = db.query(BusinessProfile).filter(BusinessProfile.id == payload.business_profile_id).first()
    if not profile:
        profile = db.query(BusinessProfile).first()

    if payload.profile_override:
        profile_data = payload.profile_override.model_dump()
    elif profile:
        profile_data = {
            "company_name": profile.company_name,
            "industry": profile.industry,
            "description": profile.description,
            "services": profile.services,
            "target_audience": profile.target_audience,
            "target_geography": profile.target_geography,
            "monthly_budget": profile.monthly_budget,
            "main_objective": profile.main_objective,
            "competitors": profile.competitors,
            "preferred_channels": profile.preferred_channels
        }
    else:
        raise HTTPException(status_code=400, detail="No business profile found. Please create one or provide profile details.")

    strategy, meta = await generate_growth_strategy(
        db,
        profile_data,
        profile.id if profile else None,
        force_demo_mode=payload.force_demo_mode
    )
    return {
        "strategy": strategy,
        "metadata": meta
    }

@router.get("/strategies", response_model=List[GrowthStrategyResponse])
def get_strategies(db: Session = Depends(get_db)):
    return db.query(GrowthStrategy).order_by(GrowthStrategy.created_at.desc()).all()

@router.get("/strategies/{strategy_id}", response_model=GrowthStrategyResponse)
def get_single_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strat = db.query(GrowthStrategy).filter(GrowthStrategy.id == strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strat

@router.post("/ai/strategy/regenerate-section")
async def regenerate_section(payload: StrategySectionRegenerateRequest, db: Session = Depends(get_db)):
    strat = db.query(GrowthStrategy).filter(GrowthStrategy.id == payload.strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")

    profile = strat.business_profile or db.query(BusinessProfile).first()
    profile_dict = {
        "company_name": profile.company_name if profile else "NovaTech Solutions",
        "industry": profile.industry if profile else "B2B Tech",
        "services": profile.services if profile else ["AI Development"],
        "target_geography": profile.target_geography if profile else ["Australia", "US", "India"],
        "monthly_budget": profile.monthly_budget if profile else 5000
    }

    fresh = generate_fallback_strategy(profile_dict)
    sec = payload.section_name
    if hasattr(strat, sec) and sec in fresh:
        setattr(strat, sec, fresh[sec])
        db.commit()
        db.refresh(strat)
        return {"section": sec, "updated_content": fresh[sec]}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid section name '{sec}'")
