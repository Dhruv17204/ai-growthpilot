import io
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_authenticated_user
from app.models.models import CampaignMetric
from app.schemas.schemas import (
    AnalyticsOverviewResponse,
    CampaignMetricResponse,
    CampaignMetricsImportResult
)
from app.services.analytics_service import get_analytics_overview, import_campaign_metrics

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(require_authenticated_user)])

MAX_UPLOAD_SIZE = 5 * 1024 * 1024 # 5 MB

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    return get_analytics_overview(db)

@router.get("/campaign-metrics", response_model=List[CampaignMetricResponse])
def get_campaign_metrics(
    campaign_id: Optional[int] = Query(None, description="Optional campaign ID filter"),
    db: Session = Depends(get_db)
):
    query = db.query(CampaignMetric)
    if campaign_id is not None:
        query = query.filter(CampaignMetric.campaign_id == campaign_id)
    return query.order_by(CampaignMetric.metric_date.desc()).all()

@router.post("/campaign-metrics/import", response_model=CampaignMetricsImportResult)
async def import_metrics_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    # Bounded chunked streaming read to prevent unbounded memory consumption
    total_bytes = 0
    chunks = []
    chunk_size = 64 * 1024  # 64 KB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024*1024)}MB."
            )
        chunks.append(chunk)

    raw_data = b"".join(chunks)

    try:
        try:
            content_str = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            content_str = raw_data.decode("latin-1")

        df = pd.read_csv(io.StringIO(content_str))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")

    if len(df) > 5000:
        raise HTTPException(status_code=400, detail="CSV contains too many rows (maximum 5,000 allowed).")

    result = import_campaign_metrics(db, df, is_demo=False)
    return result
