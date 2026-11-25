import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data_service import seed_database
from app.routers import (
    health_router,
    profile_router,
    strategy_router,
    campaign_router,
    content_router,
    leads_router,
    prompt_lab_router,
    analytics_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("growthpilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    
    # Seed default demonstration data if not present
    db = SessionLocal()
    try:
        seed_database(db, force_reset=False)
    finally:
        db.close()
    
    logger.info("AI GrowthPilot Backend successfully initialized.")
    yield
    logger.info("AI GrowthPilot Backend shutting down.")

app = FastAPI(
    title="AI GrowthPilot API",
    description="Backend API for AI GrowthPilot — Business Growth & Marketing Automation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = settings.cors_origin_list
has_wildcard = "*" in origins or not origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not has_wildcard else ["*"],
    allow_credentials=not has_wildcard,  # Wildcard origins cannot be used with allow_credentials=True per CORS spec
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept", "Origin"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

# Register routers under /api
app.include_router(health_router.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")
app.include_router(strategy_router.router, prefix="/api")
app.include_router(campaign_router.router, prefix="/api")
app.include_router(content_router.router, prefix="/api")
app.include_router(leads_router.router, prefix="/api")
app.include_router(prompt_lab_router.router, prefix="/api")
app.include_router(analytics_router.router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": "AI GrowthPilot",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }
