import math
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.auth import (
    create_session_token,
    create_csrf_token,
    validate_session_token,
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


def test_sliding_window_rate_limiter_deterministic():
    """
    Deterministic unit test for LoginRateLimiter verifying:
    - Exactly 5 failed attempts allowed in a rolling 60s window.
    - 6th attempt receives 429 with correct Retry-After.
    - Expiration of failures after 60s rolls the window forward.
    - Failures spread across >60s do not accumulate towards lockout.
    - Separate IP addresses maintain isolated failure windows.
    - Successful login resets tracking.
    """
    from app.services.rate_limiter import LoginRateLimiter

    current_time = 1000.0

    def mock_clock() -> float:
        return current_time

    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0, clock=mock_clock)

    ip1 = "192.168.1.10"
    ip2 = "192.168.1.20"

    # 1. First 4 failures on IP 1
    for i in range(4):
        current_time += 1.0
        allowed, retry = limiter.check_allowed(ip1)
        assert allowed is True
        assert retry == 0
        count, locked_retry = limiter.record_failure(ip1)
        assert count == i + 1
        assert locked_retry is None

    # 2. 5th failure on IP 1 hits threshold
    current_time += 1.0
    allowed, retry = limiter.check_allowed(ip1)
    assert allowed is True
    count, locked_retry = limiter.record_failure(ip1)
    assert count == 5
    assert locked_retry is not None
    assert locked_retry > 0

    # 3. Next attempt (6th) is rejected with 429 Retry-After
    allowed, retry = limiter.check_allowed(ip1)
    assert allowed is False
    assert retry == math.ceil(1001.0 + 60.0 - current_time)

    # 4. Independent IP 2 is unaffected
    allowed_ip2, retry_ip2 = limiter.check_allowed(ip2)
    assert allowed_ip2 is True
    assert retry_ip2 == 0

    # 5. Advance time to 1061.5: cutoff is 1061.5 - 60 = 1001.5.
    # Only t=1001 has expired. 4 failures remain in window [1002, 1003, 1004, 1005].
    current_time = 1061.5
    allowed, retry = limiter.check_allowed(ip1)
    assert allowed is True
    assert retry == 0

    # Recording another failure reaches 5 again
    count, locked_retry = limiter.record_failure(ip1)
    assert count == 5
    assert locked_retry is not None

    # 6. Success resets IP 1 completely
    limiter.record_success(ip1)
    allowed, retry = limiter.check_allowed(ip1)
    assert allowed is True
    assert retry == 0


def test_logout_csrf_protection_scenarios(client, monkeypatch):
    """
    Dedicated test suite for /auth/logout CSRF protection:
    - Session-backed logout requires both CSRF header and cookie.
    - Constant-time comparison between header and cookie.
    - Validates signature, expiry, and session binding.
    - Rejects missing, mismatched, tampered, or cross-session tokens with HTTP 403.
    - Session is NOT revoked when CSRF check fails.
    - Legitimate logout revokes session server-side.
    - Expired/unauthenticated requests clean up cookies gracefully.
    """
    from app.models.models import UserSession
    from tests.conftest import TestingSessionLocal

    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "SecureLogoutTestPass2026!")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test_admin_key")

    def login_and_get_session():
        client.cookies.clear()
        res = client.post("/api/auth/login", json={"password": "SecureLogoutTestPass2026!"})
        assert res.status_code == 200
        sess_token = res.cookies[SESSION_COOKIE_NAME]
        csrf_tok = res.cookies[CSRF_COOKIE_NAME]
        sess_id = sess_token.split(":")[1]
        client.cookies.clear()
        return sess_token, csrf_tok, sess_id

    # Scenario 1: Active session, missing CSRF header -> 403, session NOT revoked
    sess_token, csrf_tok, sess_id = login_and_get_session()
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token, CSRF_COOKIE_NAME: csrf_tok}
    )
    assert res.status_code == 403
    assert "Missing CSRF token" in res.json()["detail"]
    # Verify session is STILL active in DB
    db = TestingSessionLocal()
    try:
        record = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record is not None and not record.is_revoked
    finally:
        db.close()

    # Scenario 2: Active session, missing CSRF cookie -> 403, session NOT revoked
    client.cookies.clear()
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token},
        headers={"X-CSRF-Token": csrf_tok}
    )
    assert res.status_code == 403
    assert "Missing CSRF token" in res.json()["detail"]
    db = TestingSessionLocal()
    try:
        record = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record is not None and not record.is_revoked
    finally:
        db.close()

    # Scenario 3: Mismatched CSRF header and cookie -> 403, session NOT revoked
    other_csrf = create_csrf_token(session_id="other_session")
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token, CSRF_COOKIE_NAME: csrf_tok},
        headers={"X-CSRF-Token": other_csrf}
    )
    assert res.status_code == 403
    assert "Token mismatch" in res.json()["detail"]
    db = TestingSessionLocal()
    try:
        record = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record is not None and not record.is_revoked
    finally:
        db.close()

    # Scenario 4: Tampered signature -> 403, session NOT revoked
    tampered_csrf = csrf_tok[:-4] + "dead"
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token, CSRF_COOKIE_NAME: tampered_csrf},
        headers={"X-CSRF-Token": tampered_csrf}
    )
    assert res.status_code == 403
    assert "Invalid, expired, or session-mismatched" in res.json()["detail"]
    db = TestingSessionLocal()
    try:
        record = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record is not None and not record.is_revoked
    finally:
        db.close()

    # Scenario 5: Cross-session CSRF token (valid signature, but bound to session B) -> 403, session NOT revoked
    sess_b_token, csrf_b, sess_b_id = login_and_get_session()
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token, CSRF_COOKIE_NAME: csrf_b},
        headers={"X-CSRF-Token": csrf_b}
    )
    assert res.status_code == 403
    assert "Invalid, expired, or session-mismatched" in res.json()["detail"]
    db = TestingSessionLocal()
    try:
        record_a = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record_a is not None and not record_a.is_revoked
    finally:
        db.close()

    # Scenario 6: Legitimate logout with exact matching session-bound CSRF -> 200, session revoked
    res = client.post(
        "/api/auth/logout",
        cookies={SESSION_COOKIE_NAME: sess_token, CSRF_COOKIE_NAME: csrf_tok},
        headers={"X-CSRF-Token": csrf_tok}
    )
    assert res.status_code == 200
    assert "Logged out successfully" in res.json()["message"]
    db = TestingSessionLocal()
    try:
        record_a = db.query(UserSession).filter(UserSession.session_id == sess_id).first()
        assert record_a is not None and record_a.is_revoked
    finally:
        db.close()

    # Scenario 7: Unauthenticated logout or dead session -> 200, cleans cookies
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert "Logged out successfully" in res.json()["message"]


def test_rfc9110_http_methods_and_csrf_policy(client, monkeypatch):
    """
    Verifies that per RFC 9110 and application policy:
    - TRACE is explicitly rejected with 405 Method Not Allowed.
    - Non-exempt / unrecognized methods (CUSTOM, PURGE) fail closed and require CSRF.
    - Safe methods (GET, HEAD, OPTIONS) bypass CSRF.
    """
    from app.auth import create_server_session
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        session_token, session_id = create_server_session(db, role="admin")
    finally:
        db.close()

    # 1. TRACE method on application endpoint returns 405 Method Not Allowed
    res_trace = client.request("TRACE", "/api/leads", cookies={SESSION_COOKIE_NAME: session_token})
    assert res_trace.status_code == 405

    # 2. Non-exempt / unexpected method (e.g. PURGE) tested against require_authenticated_user
    # proves that arbitrary/unrecognized methods fail closed with 403 when CSRF is omitted
    from unittest.mock import MagicMock
    from fastapi import HTTPException
    from app.auth import require_authenticated_user

    mock_request = MagicMock()
    mock_request.method = "PURGE"
    mock_request.cookies = {SESSION_COOKIE_NAME: session_token}
    mock_request.headers = {}
    with pytest.raises(HTTPException) as exc_info:
        require_authenticated_user(mock_request, header_key=None, bearer_creds=None, db=db)
    assert exc_info.value.status_code == 403
    assert "CSRF validation failed" in exc_info.value.detail

    # 3. Safe methods (GET, HEAD, OPTIONS) bypass CSRF per RFC 9110 allowlist
    for safe_method in ["GET", "HEAD", "OPTIONS"]:
        mock_safe_req = MagicMock()
        mock_safe_req.method = safe_method
        mock_safe_req.cookies = {SESSION_COOKIE_NAME: session_token}
        mock_safe_req.headers = {}
        assert require_authenticated_user(mock_safe_req, header_key=None, bearer_creds=None, db=db) is True

    # 4. HTTP endpoint invocation: safe GET request bypasses CSRF and returns 200
    res_get = client.get("/api/leads", cookies={SESSION_COOKIE_NAME: session_token})
    assert res_get.status_code == 200


def test_login_rate_limiter_concurrency_barrier():
    """
    Deterministic concurrency test using threading.Barrier:
    - 10 threads attempt to acquire login slots simultaneously for the same IP.
    - Exactly 5 threads acquire slots (in-flight reaches 5).
    - Exactly 5 threads are denied with (False, retry_after >= 1).
    - As the 5 permitted threads record failure, in-flight drops to 0 and failures reaches 5.
    - Subsequent attempts are denied with HTTP 429 Retry-After.
    """
    import threading
    from app.services.rate_limiter import LoginRateLimiter

    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0)
    ip = "203.0.113.10"
    num_threads = 10
    barrier = threading.Barrier(num_threads)
    results = []
    lock = threading.Lock()

    def worker():
        barrier.wait()  # Synchronize thread start
        allowed, retry_after = limiter.acquire(ip)
        with lock:
            results.append((allowed, retry_after))

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly 5 should be permitted, exactly 5 denied
    permitted = [r for r in results if r[0] is True]
    denied = [r for r in results if r[0] is False]
    assert len(permitted) == 5, f"Expected 5 permitted, got {len(permitted)}"
    assert len(denied) == 5, f"Expected 5 denied, got {len(denied)}"
    for _, retry in denied:
        assert retry >= 1

    # Currently 5 attempts are in-flight
    assert limiter.in_flight_count(ip) == 5

    # Simulate threads finalizing as failures
    for _ in range(5):
        limiter.record_failure(ip)

    # In-flight count returns to 0, failures count is 5
    assert limiter.in_flight_count(ip) == 0
    assert limiter.failure_count(ip) == 5

    # Any new attempt is denied
    allowed, retry = limiter.check_allowed(ip)
    assert allowed is False
    assert retry >= 1


def test_login_rate_limiter_concurrent_isolated_ips():
    """
    Verifies that concurrent requests from distinct IPs maintain independent tracking.
    10 threads total: 5 for IP A and 5 for IP B. All 10 must succeed in acquiring slots concurrently.
    """
    import threading
    from app.services.rate_limiter import LoginRateLimiter

    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0)
    ip_a = "198.51.100.1"
    ip_b = "198.51.100.2"

    barrier = threading.Barrier(10)
    results_a = []
    results_b = []
    lock = threading.Lock()

    def worker_a():
        barrier.wait()
        res = limiter.acquire(ip_a)
        with lock:
            results_a.append(res)

    def worker_b():
        barrier.wait()
        res = limiter.acquire(ip_b)
        with lock:
            results_b.append(res)

    threads_a = [threading.Thread(target=worker_a) for _ in range(5)]
    threads_b = [threading.Thread(target=worker_b) for _ in range(5)]
    all_threads = threads_a + threads_b

    for t in all_threads:
        t.start()
    for t in all_threads:
        t.join()

    assert len(results_a) == 5
    assert all(r[0] is True for r in results_a)
    assert len(results_b) == 5
    assert all(r[0] is True for r in results_b)

    # 6th attempt on IP A is denied; IP B is independently at capacity
    assert limiter.check_allowed(ip_a)[0] is False
    assert limiter.check_allowed(ip_b)[0] is False


def test_login_rate_limiter_concurrent_success_reset():
    """
    Verifies that a successful login in the presence of concurrent failed attempts
    resets the client's failure history and releases in-flight slots cleanly.
    """
    from app.services.rate_limiter import LoginRateLimiter

    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0)
    ip = "203.0.113.50"

    # 4 failures recorded
    for _ in range(4):
        with limiter.attempt(ip) as (allowed, retry, slot):
            assert allowed is True
            slot.mark_failure()

    assert limiter.failure_count(ip) == 4
    assert limiter.in_flight_count(ip) == 0

    # 5th attempt succeeds
    with limiter.attempt(ip) as (allowed, retry, slot):
        assert allowed is True
        slot.mark_success()

    # Success resets failed attempts to 0
    assert limiter.failure_count(ip) == 0
    assert limiter.in_flight_count(ip) == 0

    # Next attempt is permitted immediately
    allowed, retry = limiter.check_allowed(ip)
    assert allowed is True
    assert retry == 0


def test_login_rate_limiter_rolling_window_boundary_retry_after():
    """
    Verifies Retry-After calculation and rolling window boundary condition.
    At oldest + 60.0:
    - Prior to boundary, retry_after is exact seconds until earliest expiry.
    - At or after boundary, oldest failure is pruned and capacity is restored.
    """
    from app.services.rate_limiter import LoginRateLimiter

    now = 5000.0

    def mock_clock():
        return now

    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0, clock=mock_clock)
    ip = "203.0.113.99"

    # Record 5 failures at t=5000, 5001, 5002, 5003, 5004
    for i in range(5):
        now = 5000.0 + i
        with limiter.attempt(ip) as (allowed, retry, slot):
            assert allowed is True
            slot.mark_failure()

    # At t=5004.2: oldest failure is at 5000.0, expires at 5060.0.
    now = 5004.2
    allowed, retry = limiter.check_allowed(ip)
    assert allowed is False
    # 5060.0 - 5004.2 = 55.8 -> ceil is 56
    assert retry == math.ceil(5000.0 + 60.0 - now)
    assert retry == 56

    # At t=5059.9: still in window, ceil(5060.0 - 5059.9) = 1
    now = 5059.9
    allowed, retry = limiter.check_allowed(ip)
    assert allowed is False
    assert retry == 1

    # At t=5060.0: boundary reached! Oldest failure (5000.0) expires.
    # 4 failures remain: [5001, 5002, 5003, 5004]
    now = 5060.0
    allowed, retry = limiter.check_allowed(ip)
    assert allowed is True
    assert retry == 0


def test_concurrent_login_endpoint_burst(monkeypatch):
    """
    End-to-end FastAPI endpoint concurrency test:
    Executes 10 concurrent POST /api/auth/login requests from the same IP with wrong password.
    Proves that exactly 5 requests return 401 Unauthorized (admitted and failed),
    and remaining requests receive 429 Too Many Requests with valid Retry-After headers.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from app.main import app
    from app.services.rate_limiter import login_rate_limiter

    login_rate_limiter.reset()
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "ConcurrentSecret2026!")

    barrier = threading.Barrier(10)
    results = []
    lock = threading.Lock()

    def send_login_request(attempt_idx: int):
        thread_client = TestClient(app)
        barrier.wait()
        res = thread_client.post(
            "/api/auth/login",
            json={"password": f"WrongPass_{attempt_idx}"}
        )
        with lock:
            results.append((res.status_code, res.headers.get("Retry-After")))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_login_request, i) for i in range(10)]
        for f in futures:
            f.result()

    status_401s = [r for r in results if r[0] == 401]
    status_429s = [r for r in results if r[0] == 429]

    assert len(status_401s) == 5, f"Expected exactly 5 401s, got {len(status_401s)}"
    assert len(status_429s) == 5, f"Expected exactly 5 429s, got {len(status_429s)}"
    for _, retry_header in status_429s:
        assert retry_header is not None
        assert int(retry_header) > 0

    login_rate_limiter.reset()




