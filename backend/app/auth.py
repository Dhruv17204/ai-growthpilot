"""
Authentication & Authorization Module for AI GrowthPilot.

Provides session-based HttpOnly cookies, server-side session tracking & revocation,
CSRF protection, constant-time API key comparisons, loopback client resolution, and fail-closed remote access.
"""
import time
import datetime
import hmac
import hashlib
import secrets
from typing import Optional, Set, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from app.models.models import UserSession

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

def create_server_session(
    db: Session,
    role: str = "admin",
    expiry_seconds: Optional[int] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[str, str]:
    """
    Creates a server-side tracked session in the database and returns (signed_token, session_id).
    """
    session_id = secrets.token_hex(32)
    duration = expiry_seconds if expiry_seconds is not None else settings.SESSION_MAX_AGE_SECONDS
    now = int(time.time())
    expiry_epoch = now + duration
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)

    session_record = UserSession(
        session_id=session_id,
        role=role,
        expires_at=expires_at,
        is_revoked=False,
        client_ip=client_ip,
        user_agent=user_agent
    )
    db.add(session_record)
    db.commit()

    payload = f"{role}:{session_id}:{expiry_epoch}"
    sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}", session_id

def revoke_session(db: Session, session_id: str) -> bool:
    """Revokes an active session record server-side."""
    record = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if record:
        record.is_revoked = True
        record.revoked_at = datetime.datetime.utcnow()
        db.commit()
        return True
    return False

def validate_session_token(token: Optional[str], db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    Validates signature, expiration, and server-side revocation status of a session token.
    Uses constant-time comparison for HMAC signature check.
    """
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

    # Server-side session verification if database session provided
    if db is not None:
        record = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if record is not None:
            if record.is_revoked:
                return None
            if record.expires_at <= datetime.datetime.utcnow():
                return None
            role = record.role
        elif settings.ENVIRONMENT.lower() == "production":
            # In production, every active session must have a corresponding database record
            return None

    return {"session_id": session_id, "role": role, "expiry": expiry}

def create_csrf_token(session_id: Optional[str] = None) -> str:
    """Creates a signed, expiring CSRF token cryptographically bound to a session ID."""
    nonce = secrets.token_hex(16)
    expiry = int(time.time()) + 86400  # 24 hours
    bound_id = session_id.strip() if session_id else "anon"
    payload = f"csrf:{bound_id}:{nonce}:{expiry}"
    sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def validate_csrf_token(token: Optional[str], expected_session_id: Optional[str] = None) -> bool:
    """
    Validates signature, expiration, and session-binding of a CSRF token.
    Uses constant-time comparison for HMAC signature check.
    """
    if not token or not isinstance(token, str):
        return False
    parts = token.split(":")
    if len(parts) == 5 and parts[0] == "csrf":
        _, bound_id, nonce, expiry_str, sig = parts
        payload = f"csrf:{bound_id}:{nonce}:{expiry_str}"
    elif len(parts) == 4 and parts[0] == "csrf":
        # Fallback/legacy format: csrf:{nonce}:{expiry}:{sig}
        _, nonce, expiry_str, sig = parts
        bound_id = None
        payload = f"csrf:{nonce}:{expiry_str}"
    else:
        return False

    expected_sig = hmac.new(settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(sig, expected_sig):
        return False
    try:
        expiry = int(expiry_str)
        if expiry <= int(time.time()):
            return False
    except ValueError:
        return False

    # Enforce session-binding when expected_session_id is provided
    if expected_session_id is not None:
        if bound_id is None or not secrets.compare_digest(bound_id, expected_session_id):
            return False

    return True

def require_authenticated_user(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> bool:
    """
    Unified security dependency protecting authenticated endpoints.
    
    Authentication mechanisms:
    1. Header authentication: X-API-Key or Bearer token matched via constant-time comparison.
    2. Server-managed session: Valid HttpOnly session cookie ('growthpilot_session') with server-side revocation check.
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
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid API key or Bearer token.",
                headers={"WWW-Authenticate": "Bearer or X-API-Key"}
            )

    # 2. Check Session Cookie (with server-side revocation and CSRF validation)
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_info = validate_session_token(session_cookie, db=db)
        if session_info:
            session_id = session_info.get("session_id")
            # Enforce CSRF protection for state-changing HTTP methods
            if request.method in STATE_CHANGING_METHODS:
                csrf_header = request.headers.get("X-CSRF-Token")
                csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
                # 1. Both header and cookie must be present
                if not csrf_header or not csrf_cookie:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF validation failed: Missing CSRF token in header or cookie."
                    )
                # 2. Header and cookie must match exactly (Double Submit)
                if not secrets.compare_digest(csrf_header, csrf_cookie):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF validation failed: Token mismatch between header and cookie."
                    )
                # 3. Signature, expiration, and session-binding validation
                if not validate_csrf_token(csrf_header, expected_session_id=session_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF validation failed: Invalid, expired, or session-mismatched CSRF token."
                    )
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked. Please log in again."
            )

    # 3. Local Loopback Fallback (Only valid when ADMIN_API_KEY is not set)
    client_ip = get_client_ip(request)
    if not admin_key:
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: Unauthenticated loopback access is disabled in production.",
                headers={"WWW-Authenticate": "Bearer or X-API-Key"}
            )
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
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> bool:
    """Dependency for administrative / destructive actions."""
    require_authenticated_user(request, header_key, bearer_creds, db=db)
    # If authenticated via session cookie, verify role == 'admin'
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_info = validate_session_token(session_cookie, db=db)
        if session_info and session_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Admin privileges required."
            )
    return True

# Backward-compatible alias
require_admin_or_local = require_admin_user
