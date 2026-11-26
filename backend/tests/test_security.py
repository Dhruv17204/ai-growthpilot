import io
import pytest
from app.services.prompt_service import redact_sensitive_text, redact_structure
from app.config import settings

def test_prompt_redaction_removes_sensitive_data():
    raw_text = (
        "Contact CEO at john.doe@enterprise.com or call +1 (555) 234-5678. "
        "Secret token: AIzaSyD98374823498234_23849234823948."
    )
    sanitized = redact_sensitive_text(raw_text)
    assert "john.doe@enterprise.com" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "(555) 234-5678" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "AIzaSy" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized

def test_prompt_structure_redaction():
    data = {
        "user": "Alice",
        "email": "alice@startup.co",
        "contacts": ["bob@corp.io", "call 415-555-1212"]
    }
    redacted = redact_structure(data)
    assert redacted["email"] == "[REDACTED_EMAIL]"
    assert redacted["contacts"][0] == "[REDACTED_EMAIL]"
    assert "[REDACTED_PHONE]" in redacted["contacts"][1]

def test_csv_upload_size_limit_rejection(client):
    # Create file > 5MB to test 413 Payload Too Large
    large_csv = b"name,company,email\n" + (b"A,B,c@d.com\n" * 500000) # ~6 MB
    file_obj = io.BytesIO(large_csv)
    res = client.post(
        "/api/leads/import",
        files={"file": ("large.csv", file_obj, "text/csv")}
    )
    assert res.status_code == 413
    assert "exceeds maximum limit" in res.json()["detail"]

def test_csv_row_limit_enforcement(client):
    # Valid size (< 5MB) but exceeds 5,000 rows
    rows = b"name,company,email\n" + (b"John Doe,Acme,john@acme.com\n" * 5001)
    file_obj = io.BytesIO(rows)
    res = client.post(
        "/api/leads/import",
        files={"file": ("many_rows.csv", file_obj, "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["successful_imports"] == 0
    assert any("5,000 rows" in err for err in data["errors"])

def test_admin_protection_when_admin_key_set(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "super_secret_admin_token")

    # Unauthorized attempt to reset demo data
    res_unauth = client.post("/api/settings/reset-demo")
    assert res_unauth.status_code == 401

    # Authorized attempt with X-API-Key
    res_auth = client.post(
        "/api/settings/reset-demo",
        headers={"X-API-Key": "super_secret_admin_token"}
    )
    assert res_auth.status_code == 200


def test_retention_worker_cleans_old_prompt_executions():
    import datetime
    from app.models.models import PromptExecution
    from app.services.retention_worker import PeriodicRetentionWorker
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        now = datetime.datetime.utcnow()
        # Old record (35 days old)
        old_exec = PromptExecution(
            feature_name="Strategy",
            prompt_version="v3.0",
            prompt_rendered="Old prompt",
            model_used="gemini-2.5-flash",
            execution_status="success",
            created_at=now - datetime.timedelta(days=35)
        )
        # Recent record (5 days old)
        recent_exec = PromptExecution(
            feature_name="Strategy",
            prompt_version="v3.0",
            prompt_rendered="Recent prompt",
            model_used="gemini-2.5-flash",
            execution_status="success",
            created_at=now - datetime.timedelta(days=5)
        )
        db.add_all([old_exec, recent_exec])
        db.commit()
        old_id = old_exec.id
        recent_id = recent_exec.id
    finally:
        db.close()

    worker = PeriodicRetentionWorker(retention_days=30, session_factory=TestingSessionLocal)
    deleted = worker.run_cleanup_once()
    assert deleted >= 1

    db2 = TestingSessionLocal()
    try:
        assert db2.query(PromptExecution).filter(PromptExecution.id == old_id).first() is None
        assert db2.query(PromptExecution).filter(PromptExecution.id == recent_id).first() is not None
    finally:
        db2.close()


def test_retention_worker_handles_database_error_gracefully(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.retention_worker import PeriodicRetentionWorker

    mock_session_factory = MagicMock(side_effect=Exception("Database connection timeout"))
    worker = PeriodicRetentionWorker(session_factory=mock_session_factory)
    # Must not raise an exception; returns 0
    deleted = worker.run_cleanup_once()
    assert deleted == 0


@pytest.mark.asyncio
async def test_retention_worker_lifecycle():
    from app.services.retention_worker import PeriodicRetentionWorker
    from tests.conftest import TestingSessionLocal

    worker = PeriodicRetentionWorker(interval_seconds=3600, session_factory=TestingSessionLocal)
    worker.start()
    assert worker._task is not None
    assert worker._is_running is True

    await worker.stop()
    assert worker._is_running is False
    assert worker._task.done()

