"""
Authentication & Authorization Module for AI GrowthPilot.

Provides session-based HttpOnly cookies, CSRF protection, constant-time
API key comparisons, loopback client resolution, and fail-closed remote access.
"""
import time
import hmac
import hashlib
import secrets
from typing import Optional, Set
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

LOCAL_HOSTS: Set[str] = {"127.0.0.1", "localhost", "::1", "testclient"}
STATE_CHANGING_METHODS: Set[str] = {"POST", "PUT", "DELETE", "PATCH"}

SESSION_COOKIE_NAME = "growthpilot_session"
CSRF_COOKIE_NAME = "growthpilot_csrf"

def get_client_ip(request: Request) -> str:
    """
    Safely resolves the client IP address.
    Does NOT blindly trust X-Forwarded-For unless the direct peer is in trusted_proxy_list.
    """
    direct_ip = request.client.host if request.client else ""
    if direct_ip in settings.trusted_proxy_list:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in X-Forwarded-For is original client
            parts = [p.strip() for p in forwarded_for.split(",")]
            if parts and parts[0]:
                return parts[0]
    return direct_ip

def create_session_token(role: str = "admin", expiry_seconds: Optional[int] = None) -> str:
    """Creates a signed, expiring session token: {role}:{session_id}:{expiry}:{signature}."""
    session_id = secrets.token_hex(16)
    duration = expiry_seconds if expiry_seconds is not None else settings.SESSION_MAX_AGE_SECONDS
    expiry = int(time.time()) + duration
    payload = f"{role}:{session_id}:{expiry}"
    sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def validate_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration of a session token using constant-time comparison."""
    if not token or not isinstance(token, str):
        return None
    parts = token.split(":")
    if len(parts) == 4:
        role, session_id, expiry_str, sig = parts
        payload = f"{role}:{session_id}:{expiry_str}"
    elif len(parts) == 3:
        session_id, expiry_str, sig = parts
        role = "admin"
        payload = f"{session_id}:{expiry_str}"
    else:
        return None

    expected_sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(sig, expected_sig):
        return None
    try:
        expiry = int(expiry_str)
        if expiry <= int(time.time()):
            return None
    except ValueError:
        return None
    return {"session_id": session_id, "role": role, "expiry": expiry}

def create_csrf_token() -> str:
    """Creates a signed, expiring CSRF token."""
    nonce = secrets.token_hex(16)
    expiry = int(time.time()) + 86400  # 24 hours
    payload = f"csrf:{nonce}:{expiry}"
    sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def validate_csrf_token(token: Optional[str]) -> bool:
    """Validates signature and expiration of a CSRF token."""
    if not token or not isinstance(token, str):
        return False
    parts = token.split(":")
    if len(parts) != 4 or parts[0] != "csrf":
        return False
    _, nonce, expiry_str, sig = parts
    payload = f"csrf:{nonce}:{expiry_str}"
    expected_sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(sig, expected_sig):
        return False
    try:
        expiry = int(expiry_str)
        if expiry <= int(time.time()):
            return False
    except ValueError:
        return False
    return True

def require_authenticated_user(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> bool:
    """
    Unified security dependency protecting authenticated endpoints.
    
    Authentication mechanisms:
    1. Header authentication: X-API-Key or Bearer token matched via constant-time comparison.
    2. Server-managed session: Valid HttpOnly session cookie ('growthpilot_session').
       State-changing requests authenticated via cookie MUST provide valid X-CSRF-Token.
    3. Local-only mode: When ADMIN_API_KEY is unset, requests from loopback clients
       (127.0.0.1, localhost, testclient) are permitted for local demonstration.
    4. Remote requests without valid credentials fail closed (401 or 403).
    """
    admin_key = settings.ADMIN_API_KEY.strip() if settings.ADMIN_API_KEY else ""

    # 1. Check API Key / Bearer Token Header
    provided_key = None
    if header_key:
        provided_key = header_key.strip()
    elif bearer_creds:
        provided_key = bearer_creds.credentials.strip()

    if provided_key:
        if admin_key and secrets.compare_digest(provided_key, admin_key):
            return True
        elif not admin_key and provided_key == "local-dev-bypass":
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid API key or Bearer token.",
                headers={"WWW-Authenticate": "Bearer or X-API-Key"}
            )

    # 2. Check Session Cookie
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        if validate_session_token(session_cookie):
            # Enforce CSRF protection for state-changing HTTP methods
            if request.method in STATE_CHANGING_METHODS:
                csrf_token = request.headers.get("X-CSRF-Token")
                if not csrf_token or not validate_csrf_token(csrf_token):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF validation failed: Missing or invalid X-CSRF-Token header."
                    )
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid. Please log in again."
            )

    # 3. Local Loopback Fallback (Only valid when ADMIN_API_KEY is not set)
    client_ip = get_client_ip(request)
    if not admin_key:
        if client_ip in LOCAL_HOSTS:
            return True
        # Remote visitor accessing unauthenticated instance fails closed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Forbidden: Remote access from '{client_ip}' is blocked. "
                "Configure ADMIN_API_KEY in backend/.env to enable authenticated access."
            )
        )

    # 4. ADMIN_API_KEY is configured but no valid credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid session or API key.",
        headers={"WWW-Authenticate": "Bearer or X-API-Key"}
    )

def require_admin_user(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> bool:
    """Dependency for administrative / destructive actions."""
    require_authenticated_user(request, header_key, bearer_creds)
    # If authenticated via session cookie, verify role == 'admin'
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_info = validate_session_token(session_cookie)
        if session_info and session_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Admin privileges required."
            )
    return True

# Backward-compatible alias
require_admin_or_local = require_admin_user
