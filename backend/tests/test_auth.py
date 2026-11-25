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
    session_id = token.split(":")[1]
    csrf = create_csrf_token(session_id=session_id)

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
    assert "Missing CSRF token" in res_no_csrf.json()["detail"]

    # 2. State-changing POST with wrong CSRF header -> 403 Forbidden (mismatch)
    res_wrong_csrf = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": "invalid_csrf_token"}
    )
    assert res_wrong_csrf.status_code == 403
    assert "Token mismatch" in res_wrong_csrf.json()["detail"]

    # 3. State-changing POST with missing CSRF cookie -> 403 Forbidden
    client.cookies.delete(CSRF_COOKIE_NAME)
    res_no_cookie = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": csrf}
    )
    assert res_no_cookie.status_code == 403
    assert "Missing CSRF token" in res_no_cookie.json()["detail"]

    # 4. State-changing POST with token belonging to a different session -> 403 Forbidden
    other_csrf = create_csrf_token(session_id="different_session_9999")
    client.cookies.set(CSRF_COOKIE_NAME, other_csrf)
    res_other_session = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": other_csrf}
    )
    assert res_other_session.status_code == 403
    assert "session-mismatched" in res_other_session.json()["detail"]

    # 5. State-changing POST with tampered signature -> 403 Forbidden
    tampered_csrf = csrf[:-4] + "xxxx"
    client.cookies.set(CSRF_COOKIE_NAME, tampered_csrf)
    res_tampered = client.post(
        "/api/business-profile",
        json=profile_payload,
        headers={"X-CSRF-Token": tampered_csrf}
    )
    assert res_tampered.status_code == 403
    assert "Invalid, expired, or session-mismatched" in res_tampered.json()["detail"]

    # 6. GET / HEAD requests do NOT require CSRF token
    client.cookies.delete(CSRF_COOKIE_NAME)
    res_get = client.get("/api/leads")
    assert res_get.status_code == 200

    # 7. State-changing POST with valid matching session-bound CSRF header & cookie -> 200 OK
    client.cookies.set(CSRF_COOKIE_NAME, csrf)
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


def test_production_session_secret_enforcement():
    from app.config import validate_production_session_secret, DEV_DEFAULT_SESSION_SECRET

    # 1. Production with empty secret -> raises ValueError
    with pytest.raises(ValueError, match="SESSION_SECRET is required"):
        validate_production_session_secret("", "production")

    with pytest.raises(ValueError, match="SESSION_SECRET is required"):
        validate_production_session_secret("   ", "production")

    # 2. Production with dev default secret -> raises ValueError
    with pytest.raises(ValueError, match="Default development SESSION_SECRET cannot be used"):
        validate_production_session_secret(DEV_DEFAULT_SESSION_SECRET, "production")

    # 3. Production with secret < 32 characters -> raises ValueError
    with pytest.raises(ValueError, match="too short"):
        validate_production_session_secret("short-secret-key-123", "production")

    # 4. Production with valid secret (>= 32 chars and not default) -> passes
    strong_secret = "a" * 32
    validate_production_session_secret(strong_secret, "production")  # Should not raise

    # 5. Development mode with default secret -> passes
    validate_production_session_secret(DEV_DEFAULT_SESSION_SECRET, "development")  # Should not raise


def test_server_side_session_creation_and_revocation():
    from app.auth import create_server_session, revoke_session
    from app.models.models import UserSession
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        # Create server session
        token, session_id = create_server_session(db, role="admin", client_ip="127.0.0.1")
        assert token is not None
        assert session_id is not None

        # Verify DB record exists and is active
        record = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        assert record is not None
        assert record.is_revoked is False
        assert record.role == "admin"

        # Validate token against DB
        payload = validate_session_token(token, db=db)
        assert payload is not None
        assert payload["session_id"] == session_id
        assert payload["role"] == "admin"

        # Revoke session
        success = revoke_session(db, session_id)
        assert success is True

        # Verify DB record updated
        db.refresh(record)
        assert record.is_revoked is True
        assert record.revoked_at is not None

        # Replayed token must now be rejected
        revoked_payload = validate_session_token(token, db=db)
        assert revoked_payload is None
    finally:
        db.close()


def test_logout_revokes_server_session_and_rejects_subsequent_request(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "TestPassword2026!")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test_admin_key")

    # 1. Login to get server-tracked session
    login_res = client.post("/api/auth/login", json={"password": "TestPassword2026!"})
    assert login_res.status_code == 200
    session_token = login_res.cookies[SESSION_COOKIE_NAME]
    csrf_token = login_res.cookies[CSRF_COOKIE_NAME]

    # Verify access works before logout
    headers = {"X-CSRF-Token": csrf_token}
    res_before = client.get("/api/leads", cookies={SESSION_COOKIE_NAME: session_token}, headers=headers)
    assert res_before.status_code == 200

    # 2. Logout
    logout_res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: session_token, CSRF_COOKIE_NAME: csrf_token},
        headers=headers
    )
    assert logout_res.status_code == 200

    # 3. Replay attack: try accessing protected route with the old session token
    res_after = client.get("/api/leads", cookies={SESSION_COOKIE_NAME: session_token}, headers=headers)
    assert res_after.status_code == 401
    assert "Session expired or revoked" in res_after.json()["detail"]


def test_server_side_session_expiration_rejection():
    from app.auth import create_server_session
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        # Create an expired session in DB
        token, session_id = create_server_session(db, role="admin", expiry_seconds=-10)
        payload = validate_session_token(token, db=db)
        assert payload is None
    finally:
        db.close()


def test_production_mode_requires_database_session_record(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        # Create token without server session record
        stateless_token = create_session_token(role="admin")
        # In production, stateless token without DB record must be rejected
        payload = validate_session_token(stateless_token, db=db)
        assert payload is None
    finally:
        db.close()


def test_hardcoded_dev_bypass_token_is_strictly_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

    # 1. Local client attempting X-API-Key: local-dev-bypass -> 401 Unauthorized
    res_key = client.get("/api/leads", headers={"X-API-Key": "local-dev-bypass"})
    assert res_key.status_code == 401
    assert "Invalid API key" in res_key.json()["detail"]

    # 2. Local client attempting Bearer local-dev-bypass -> 401 Unauthorized
    res_bearer = client.get("/api/leads", headers={"Authorization": "Bearer local-dev-bypass"})
    assert res_bearer.status_code == 401
    assert "Invalid API key" in res_bearer.json()["detail"]

    # 3. Remote client attempting X-API-Key: local-dev-bypass -> 401 Unauthorized
    with TestClient(client.app, client=("203.0.113.45", 50000)) as remote_client:
        res_remote = remote_client.get("/api/leads", headers={"X-API-Key": "local-dev-bypass"})
        assert res_remote.status_code == 401
        assert "Invalid API key" in res_remote.json()["detail"]


def test_unauthenticated_loopback_access_strictly_disabled_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

    # Local loopback client attempting unauthenticated access in production -> 401 Unauthorized
    res = client.get("/api/leads")
    assert res.status_code == 401
    assert "Unauthenticated loopback access is disabled in production" in res.json()["detail"]


def test_login_fails_in_production_when_admin_credentials_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

    res = client.post("/api/auth/login", json={"password": "any-password"})
    assert res.status_code == 403
    assert "must be configured in production" in res.json()["detail"]


def test_login_rate_limiting_and_brute_force_lockout(client, monkeypatch):
    from app.services.rate_limiter import login_rate_limiter
    login_rate_limiter.reset()

    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "CorrectPassword2026!")

    # Attempts 1 through 5 with wrong password -> 401 Unauthorized
    for attempt in range(1, 6):
        res = client.post("/api/auth/login", json={"password": f"WrongAttempt{attempt}"})
        assert res.status_code == 401
        assert "Invalid credentials" in res.json()["detail"]

    # 6th attempt -> 429 Too Many Requests (Lockout enforced)
    res_locked = client.post("/api/auth/login", json={"password": "CorrectPassword2026!"})
    assert res_locked.status_code == 429
    assert "Too many failed login attempts" in res_locked.json()["detail"]
    assert "Retry-After" in res_locked.headers
    retry_after = int(res_locked.headers["Retry-After"])
    assert retry_after > 0

    # Cooldown recovery: after reset, legitimate login succeeds
    login_rate_limiter.reset()
    res_success = client.post("/api/auth/login", json={"password": "CorrectPassword2026!"})
    assert res_success.status_code == 200
    assert res_success.json()["authenticated"] is True



