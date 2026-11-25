import io
import pytest
from app.services.prompt_service import redact_sensitive_text, redact_structure, log_prompt_execution
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
