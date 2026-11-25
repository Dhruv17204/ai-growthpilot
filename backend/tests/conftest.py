import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.seed_data_service import seed_database
from app.models.models import (
    BusinessProfile, GrowthStrategy, Campaign, ContentItem,
    Lead, LeadNote, PromptTemplate, PromptExecution, AIActivity, CampaignMetric
)

TEST_DB_FILE = "./test_growthpilot.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.query(LeadNote).delete()
    db.query(Lead).delete()
    db.query(ContentItem).delete()
    db.query(Campaign).delete()
    db.query(GrowthStrategy).delete()
    db.query(BusinessProfile).delete()
    db.query(PromptExecution).delete()
    db.query(PromptTemplate).delete()
    db.query(AIActivity).delete()
    db.query(CampaignMetric).delete()
    db.commit()
    seed_database(db, force_reset=False)
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

from app.auth import (
    create_session_token,
    create_csrf_token,
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_client():
    """Client with valid authenticated session cookie and matching CSRF header."""
    with TestClient(app) as c:
        token = create_session_token(role="user")
        csrf = create_csrf_token()
        c.cookies.set(SESSION_COOKIE_NAME, token)
        c.cookies.set(CSRF_COOKIE_NAME, csrf)
        c.headers.update({"X-CSRF-Token": csrf})
        yield c

@pytest.fixture
def admin_client():
    """Client with valid admin session cookie and matching CSRF header."""
    with TestClient(app) as c:
        token = create_session_token(role="admin")
        csrf = create_csrf_token()
        c.cookies.set(SESSION_COOKIE_NAME, token)
        c.cookies.set(CSRF_COOKIE_NAME, csrf)
        c.headers.update({"X-CSRF-Token": csrf})
        yield c
