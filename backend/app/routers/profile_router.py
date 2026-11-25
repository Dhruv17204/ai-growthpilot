from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import BusinessProfile
from app.schemas.schemas import BusinessProfileResponse, BusinessProfileCreate

router = APIRouter(prefix="/business-profile", tags=["Business Profile"])

@router.get("", response_model=BusinessProfileResponse)
def get_business_profile(db: Session = Depends(get_db)):
    profile = db.query(BusinessProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No business profile found. Please create one.")
    return profile

@router.post("", response_model=BusinessProfileResponse)
def create_or_update_profile(payload: BusinessProfileCreate, db: Session = Depends(get_db)):
    profile = db.query(BusinessProfile).first()
    if profile:
        profile.company_name = payload.company_name
        profile.industry = payload.industry
        profile.website = payload.website
        profile.description = payload.description
        profile.services = payload.services
        profile.target_audience = payload.target_audience
        profile.target_geography = payload.target_geography
        profile.monthly_budget = payload.monthly_budget
        profile.main_objective = payload.main_objective
        profile.competitors = payload.competitors
        profile.preferred_channels = payload.preferred_channels
    else:
        profile = BusinessProfile(
            company_name=payload.company_name,
            industry=payload.industry,
            website=payload.website,
            description=payload.description,
            services=payload.services,
            target_audience=payload.target_audience,
            target_geography=payload.target_geography,
            monthly_budget=payload.monthly_budget,
            main_objective=payload.main_objective,
            competitors=payload.competitors,
            preferred_channels=payload.preferred_channels,
            is_demo=False
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
