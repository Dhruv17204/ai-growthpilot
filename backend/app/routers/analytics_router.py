from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import AnalyticsOverviewResponse
from app.services.analytics_service import get_analytics_overview

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    return get_analytics_overview(db)
