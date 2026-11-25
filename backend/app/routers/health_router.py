from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.auth import require_authenticated_user, require_admin_user
from app.services.gemini_client import gemini_client
from app.services.seed_data_service import seed_database
from app.schemas.schemas import HealthResponse, GeminiKeyUpdateRequest

router = APIRouter(tags=["Health & Settings"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    ai_status = "connected" if gemini_client.is_configured() else "demo_simulation"
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        database="connected",
        ai_status=ai_status,
        ai_model=gemini_client.model_name,
        demo_mode=settings.DEMO_MODE or not gemini_client.is_configured()
    )

@router.get("/settings/ai-config", dependencies=[Depends(require_authenticated_user)])
async def get_ai_config():
    """Returns safe connection state without exposing secrets."""
    status_result = await gemini_client.test_connection()
    return {
        "model": gemini_client.model_name,
        "is_configured": gemini_client.is_configured(),
        "status_check": status_result,
        "masked_key": f"...{gemini_client.api_key[-4:]}" if gemini_client.api_key else "Not Configured"
    }

@router.post("/settings/gemini-key", dependencies=[Depends(require_admin_user)])
async def update_gemini_key(payload: GeminiKeyUpdateRequest):
    key = payload.gemini_api_key.strip()
    model = payload.gemini_model.strip() if payload.gemini_model else "gemini-2.5-flash"
    gemini_client.update_key(key, model)
    test_res = await gemini_client.test_connection()
    return {
        "message": "API key updated in active session.",
        "test_result": test_res
    }

@router.post("/settings/reset-demo", dependencies=[Depends(require_admin_user)])
def reset_demo_data(db: Session = Depends(get_db)):
    seed_database(db, force_reset=True)
    return {"message": "Database reset and re-seeded with NovaTech Solutions demo data."}
