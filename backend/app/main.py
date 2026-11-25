import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data_service import seed_database
from app.services.prompt_service import clean_old_prompt_executions
from app.routers import (
    auth_router,
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
        # 30-Day prompt execution data retention cleanup on startup
        deleted_prompts = clean_old_prompt_executions(db, days=30)
        if deleted_prompts > 0:
            logger.info(f"Cleaned {deleted_prompts} expired prompt executions per 30-day retention policy.")
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
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-CSRF-Token", "Accept", "Origin"],
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
app.include_router(auth_router.router, prefix="/api")
app.include_router(health_router.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")
app.include_router(strategy_router.router, prefix="/api")
app.include_router(campaign_router.router, prefix="/api")
app.include_router(content_router.router, prefix="/api")
app.include_router(leads_router.router, prefix="/api")
app.include_router(prompt_lab_router.router, prefix="/api")
app.include_router(analytics_router.router, prefix="/api")

# Single-Container Frontend Serving & React SPA Fallback
_FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if not os.path.exists(_FRONTEND_DIST):
    _FRONTEND_DIST = "/app/frontend/dist"

if os.path.exists(_FRONTEND_DIST):
    assets_dir = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_routes(full_path: str):
        # Do not intercept API or documentation routes
        if full_path.startswith("api") or full_path in ("docs", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")

        # Specific static file request in dist root (e.g. favicon.ico, manifest.json)
        file_path = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # SPA client-side fallback
        index_path = os.path.join(_FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Frontend assets not found.")
else:
    @app.get("/")
    def root():
        return {
            "app": "AI GrowthPilot",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "operational"
        }
