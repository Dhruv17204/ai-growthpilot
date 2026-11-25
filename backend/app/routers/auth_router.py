"""
Authentication Router for AI GrowthPilot.

Provides session creation, logout, CSRF token issuance, and auth status telemetry.
"""
import secrets
from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
from app.config import settings
from app.auth import (
    create_session_token,
    validate_session_token,
    create_csrf_token,
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
def login(payload: LoginRequest, request: Request, response: Response):
    expected_password = (
        settings.ADMIN_PASSWORD.strip() if settings.ADMIN_PASSWORD
        else (settings.ADMIN_API_KEY.strip() if settings.ADMIN_API_KEY else "")
    )

    if expected_password:
        if not secrets.compare_digest(payload.password.strip(), expected_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Incorrect password."
            )
    else:
        # In local unconfigured mode, any password or empty password creates a local session
        client_ip = get_client_ip(request)
        if client_ip not in LOCAL_HOSTS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Remote login unavailable when ADMIN_API_KEY is not configured."
            )

    session_token = create_session_token(role="admin")
    csrf_token = create_csrf_token()

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
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}

@router.get("/status", response_model=AuthStatusResponse)
@router.get("/me", response_model=AuthStatusResponse)
def get_auth_status(request: Request):
    client_ip = get_client_ip(request)
    is_local = client_ip in LOCAL_HOSTS
    admin_key = bool(settings.ADMIN_API_KEY.strip()) if settings.ADMIN_API_KEY else False

    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    has_valid_session = bool(validate_session_token(session_cookie)) if session_cookie else False

    authenticated = bool(has_valid_session or (not admin_key and is_local))
    csrf_token = create_csrf_token()

    return AuthStatusResponse(
        authenticated=authenticated,
        auth_required=bool(admin_key),
        is_local=is_local,
        client_ip=client_ip,
        csrf_token=csrf_token
    )

@router.get("/csrf")
def get_csrf():
    return {"csrf_token": create_csrf_token()}
