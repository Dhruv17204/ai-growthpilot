import time
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.auth import (
    create_session_token,
    create_csrf_token,
    validate_session_token,
    validate_csrf_token,
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
)

def test_public_health_endpoint_accessible_without_auth(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "ready", "degraded")

def test_auth_status_endpoint(client, auth_client):
    # Test unauthenticated / local loopback
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert "authenticated" in data
    assert "client_ip" in data

    # Test authenticated
    res_auth = auth_client.get("/api/auth/status")
    assert res_auth.status_code == 200
    assert res_auth.json()["authenticated"] is True

def test_login_success_and_cookie_generation(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "TestPassword2026!")

    # Login with valid password
    res = client.post("/api/auth/login", json={"password": "TestPassword2026!"})
    assert res.status_code == 200
    assert res.json()["authenticated"] is True
    assert SESSION_COOKIE_NAME in res.cookies
    assert CSRF_COOKIE_NAME in res.cookies

    # Verify session cookie properties
    session_val = res.cookies[SESSION_COOKIE_NAME]
    payload = validate_session_token(session_val)
    assert payload is not None
    assert payload["role"] == "admin"

def test_login_rejection_invalid_password(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "TestPassword2026!")

    res = client.post("/api/auth/login", json={"password": "WrongPassword"})
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]
    assert SESSION_COOKIE_NAME not in res.cookies

def test_logout_clears_cookies(auth_client):
    res = auth_client.post("/api/auth/logout")
    assert res.status_code == 200
    # Cookie should be expired/cleared
    assert res.cookies.get(SESSION_COOKIE_NAME) == "" or SESSION_COOKIE_NAME not in res.cookies

def test_csrf_protection_on_state_changing_requests(client):
    # Authenticated session token
    token = create_session_token(role="user")
    csrf = create_csrf_token()

    profile_payload = {
        "company_name": "TestCorp",
        "industry": "B2B SaaS",
        "description": "Enterprise software",
        "services": ["Analytics"],
        "target_audience": ["Enterprises"],
        "target_geography": ["US"],
        "monthly_budget": 5000.0,
        "main_objective": "Growth"
    }

    # 1. State-changing POST without CSRF header -> 403 Forbidden
    client.cookies.set(SESSION_COOKIE_NAME, token)
    client.cookies.set(CSRF_COOKIE_NAME, csrf)
    res_no_csrf = client.post("/api/business-profile", json=profile_payload)
    assert res_no_csrf.status_code == 403
    assert "CSRF" in res_no_csrf.json()["detail"]

    # 2. State-changing POST with wrong CSRF header -> 403 Forbidden
    res_wrong_csrf = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": "invalid_csrf_token"}
    )
    assert res_wrong_csrf.status_code == 403

    # 3. State-changing POST with valid CSRF header -> 200 OK
    res_valid = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": csrf}
    )
    assert res_valid.status_code == 200

def test_expired_session_token_rejection(client):
    # Create expired token (-60 seconds)
    expired_token = create_session_token(expiry_seconds=-60)
    csrf = create_csrf_token()

    client.cookies.set(SESSION_COOKIE_NAME, expired_token)
    client.cookies.set(CSRF_COOKIE_NAME, csrf)
    client.headers.update({"X-CSRF-Token": csrf})

    # When ADMIN_API_KEY is configured, invalid/expired session must fail with 401
    from app.config import settings
    original_key = settings.ADMIN_API_KEY
    try:
        settings.ADMIN_API_KEY = "test_admin_key"
        res = client.get("/api/leads")
        assert res.status_code == 401
    finally:
        settings.ADMIN_API_KEY = original_key

def test_tampered_session_token_rejection():
    valid_token = create_session_token()
    # Tamper with signature
    tampered = valid_token[:-4] + "xxxx"
    assert validate_session_token(tampered) is None

def test_remote_visitor_fails_closed_when_no_admin_key(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

    # Simulate remote IP via TestClient with explicit client host
    with TestClient(client.app, client=("203.0.113.45", 50000)) as remote_client:
        res = remote_client.get("/api/leads")
        assert res.status_code == 403
        assert "Remote access" in res.json()["detail"]

def test_spoofed_forwarded_for_from_untrusted_peer_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

    # Direct client is remote (203.0.113.45), pretending to be localhost via X-Forwarded-For
    with TestClient(client.app, client=("203.0.113.45", 50000)) as remote_client:
        res = remote_client.get(
            "/api/leads",
            headers={"X-Forwarded-For": "127.0.0.1"}
        )
        assert res.status_code == 403
        assert "Remote access" in res.json()["detail"]

def test_admin_role_authorization_boundary(client, auth_client, admin_client):
    # Regular user session cannot reset demo data
    res_user = auth_client.post("/api/settings/reset-demo")
    assert res_user.status_code == 403
    assert "Admin privileges required" in res_user.json()["detail"]

    # Admin session can reset demo data
    res_admin = admin_client.post("/api/settings/reset-demo")
    assert res_admin.status_code == 200
