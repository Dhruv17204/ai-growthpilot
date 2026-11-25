import io
import csv
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Lead, BusinessProfile, LeadNote
from app.schemas.schemas import (
    LeadResponse, LeadCreate, LeadUpdate, LeadNoteCreate, LeadNoteResponse, CSVImportResult
)
from app.services.lead_scoring_service import process_leads_csv, score_single_lead, heuristic_lead_score

router = APIRouter(prefix="/leads", tags=["Lead Intelligence"])

MAX_CSV_BYTES = 5 * 1024 * 1024 # 5 MB upload limit

def sanitize_csv_cell(val: Any) -> str:
    """
    Prevents CSV / DDE formula injection (CWE-1236).
    Neutralizes leading '=', '+', '-', '@', tab, and carriage return characters.
    """
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s

@router.post("/import", response_model=CSVImportResult)
async def import_leads_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a standard CSV file with .csv extension."
        )

    content = await file.read()
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds maximum limit of {MAX_CSV_BYTES // (1024 * 1024)} MB."
        )

    profile = db.query(BusinessProfile).first()
    result = process_leads_csv(db, content, profile)
    return result

@router.get("", response_model=List[LeadResponse])
def get_leads(
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: Optional[str] = "score",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    query = db.query(Lead)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Lead.name.ilike(search_pattern)) |
            (Lead.company.ilike(search_pattern)) |
            (Lead.email.ilike(search_pattern)) |
            (Lead.industry.ilike(search_pattern)) |
            (Lead.job_title.ilike(search_pattern))
        )

    if category and category != "All":
        query = query.filter(Lead.qualification_category == category)

    if status and status != "All":
        query = query.filter(Lead.status == status)

    if source and source != "All":
        query = query.filter(Lead.lead_source == source)

    if sort_by == "score":
        query = query.order_by(Lead.score.desc() if sort_order == "desc" else Lead.score.asc())
    elif sort_by == "name":
        query = query.order_by(Lead.name.asc() if sort_order == "asc" else Lead.name.desc())
    elif sort_by == "company":
        query = query.order_by(Lead.company.asc() if sort_order == "asc" else Lead.company.desc())
    else:
        query = query.order_by(Lead.created_at.desc())

    return query.all()

@router.get("/export")
def export_leads_csv(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.score.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Company", "Email", "Website", "Industry", "Job Title",
        "Location", "Company Size", "Lead Source", "Score", "Priority",
        "Status", "Business Fit Summary", "Suggested Next Action"
    ])
    for l in leads:
        # Sanitize every field to prevent CSV formula injection
        writer.writerow([
            sanitize_csv_cell(l.name),
            sanitize_csv_cell(l.company),
            sanitize_csv_cell(l.email),
            sanitize_csv_cell(l.website),
            sanitize_csv_cell(l.industry),
            sanitize_csv_cell(l.job_title),
            sanitize_csv_cell(l.location),
            sanitize_csv_cell(l.company_size),
            sanitize_csv_cell(l.lead_source),
            l.score,
            l.qualification_category,
            l.status,
            sanitize_csv_cell(l.business_fit_summary),
            sanitize_csv_cell(l.suggested_next_action)
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=growthpilot_leads_export.csv"}
    )

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = payload.dict(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(lead, field, val)

    db.commit()
    db.refresh(lead)
    return lead

@router.post("/{lead_id}/score")
async def recalculate_score(
    lead_id: int,
    force_demo_mode: bool = Query(False),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profile = db.query(BusinessProfile).first()
    score_result = await score_single_lead(db, lead, profile, force_demo_mode=force_demo_mode)
    return {
        "message": f"Lead score evaluated for {lead.name}",
        "result": score_result
    }

@router.post("/{lead_id}/notes", response_model=LeadNoteResponse)
def add_lead_note(lead_id: int, payload: LeadNoteCreate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    note = LeadNote(
        lead_id=lead.id,
        note_text=payload.note_text
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
