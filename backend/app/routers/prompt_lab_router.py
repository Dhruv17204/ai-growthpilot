from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_authenticated_user
from app.models.models import PromptTemplate, PromptExecution, AIActivity
from app.schemas.schemas import PromptTemplateResponse, PromptExecutionResponse, AIActivityResponse

router = APIRouter(tags=["Prompt Lab & Activity"], dependencies=[Depends(require_authenticated_user)])

@router.get("/prompts", response_model=List[PromptTemplateResponse])
def get_prompt_templates(db: Session = Depends(get_db)):
    return db.query(PromptTemplate).order_by(PromptTemplate.category, PromptTemplate.version).all()

@router.get("/prompts/history", response_model=List[PromptExecutionResponse])
def get_prompt_executions(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(PromptExecution).order_by(PromptExecution.created_at.desc()).limit(limit).all()

@router.get("/ai/activity", response_model=List[AIActivityResponse])
def get_ai_activities(limit: int = 25, db: Session = Depends(get_db)):
    return db.query(AIActivity).order_by(AIActivity.created_at.desc()).limit(limit).all()
