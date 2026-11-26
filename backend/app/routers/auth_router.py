"""
Authentication Router for AI GrowthPilot.

Provides session creation, logout, CSRF token issuance, and auth status telemetry.
"""
import secrets
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.config import settings
from app.database import get_db
from app.services.rate_limiter import login_rate_limiter
from app.auth import (
    create_server_session,
    revoke_session,
    validate_session_token,
    create_csrf_token,
    validate_csrf_token,
    get_client_ip,
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    LOCAL_HOSTS
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    message: str
    authenticated: bool
    csrf_token: str

class AuthStatusResponse(BaseModel):
    authenticated: bool
    auth_required: bool
    is_local: bool
    client_ip: str
    csrf_token: str

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)

    # 1. Enforce brute-force rate limiting with concurrency-safe in-flight tracking
    with login_rate_limiter.attempt(client_ip) as (is_allowed, retry_after, slot):
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

        expected_password = (
            settings.ADMIN_PASSWORD.strip() if settings.ADMIN_PASSWORD
            else (settings.ADMIN_API_KEY.strip() if settings.ADMIN_API_KEY else "")
        )

        if expected_password:
            if not secrets.compare_digest(payload.password.strip(), expected_password):
                slot.mark_failure()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials. Incorrect password."
                )
        else:
            if settings.ENVIRONMENT.lower() == "production":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Login unavailable: ADMIN_PASSWORD or ADMIN_API_KEY must be configured in production."
                )
            # In local unconfigured mode, any password or empty password creates a local session
            if client_ip not in LOCAL_HOSTS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Remote login unavailable when ADMIN_API_KEY is not configured."
                )

        # Successful authentication resets failed attempts
        slot.mark_success()

        session_token, session_id = create_server_session(
            db=db,
            role="admin",
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent")
        )
        csrf_token = create_csrf_token(session_id=session_id)

        is_prod = settings.ENVIRONMENT.lower() == "production"

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_MAX_AGE_SECONDS,
            httponly=True,
            samesite="lax",
            secure=is_prod,
            path="/"
        )

        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            max_age=settings.SESSION_MAX_AGE_SECONDS,
            httponly=False,  # Accessible to frontend JavaScript for header injection
            samesite="lax",
            secure=is_prod,
            path="/"
        )

        return LoginResponse(
            message="Session authenticated successfully.",
            authenticated=True,
            csrf_token=csrf_token
        )

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_info = validate_session_token(session_cookie, db=db)
        if session_info:
            session_id = session_info["session_id"]
            csrf_header = request.headers.get("X-CSRF-Token")
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)

            # 1. Both header and cookie must be provided
            if not csrf_header or not csrf_cookie:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed on logout: Missing CSRF token in header or cookie."
                )
            # 2. Header and cookie must match (Double Submit)
            if not secrets.compare_digest(csrf_header, csrf_cookie):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed on logout: Token mismatch between header and cookie."
                )
            # 3. Signature, expiry, and session binding
            if not validate_csrf_token(csrf_header, expected_session_id=session_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed on logout: Invalid, expired, or session-mismatched CSRF token."
                )

            # Revoke session only after CSRF checks pass
            revoke_session(db, session_id)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}

@router.get("/status", response_model=AuthStatusResponse)
@router.get("/me", response_model=AuthStatusResponse)
def get_auth_status(request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    is_local = client_ip in LOCAL_HOSTS
    admin_key = bool(settings.ADMIN_API_KEY.strip()) if settings.ADMIN_API_KEY else False

    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_info = validate_session_token(session_cookie, db=db) if session_cookie else None
    has_valid_session = bool(session_info)
    session_id = session_info.get("session_id") if session_info else None

    is_prod = settings.ENVIRONMENT.lower() == "production"

    authenticated = bool(
        has_valid_session or (not admin_key and is_local and not is_prod)
    )
    csrf_token = create_csrf_token(session_id=session_id)

    return AuthStatusResponse(
        authenticated=authenticated,
        auth_required=bool(admin_key or is_prod),
        is_local=is_local,
        client_ip=client_ip,
        csrf_token=csrf_token
    )

@router.get("/csrf")
def get_csrf(request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_info = validate_session_token(session_cookie, db=db) if session_cookie else None
    session_id = session_info.get("session_id") if session_info else None
    return {"csrf_token": create_csrf_token(session_id=session_id)}
