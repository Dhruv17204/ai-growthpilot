"""
Authentication & Authorization Module for AI GrowthPilot.

Provides local-mode verification and optional ADMIN_API_KEY protection
for sensitive mutation and administrative endpoints.
"""
from typing import Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "testclient"}

def require_admin_or_local(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> bool:
    """
    Security dependency for sensitive endpoints.
    
    1. If ADMIN_API_KEY is configured in settings:
       - Requires either `X-API-Key: <key>` or `Authorization: Bearer <key>`.
       - Rejects requests if key does not match.
    2. If ADMIN_API_KEY is NOT configured (default local evaluation / demo mode):
       - Verifies that request originates from a local loopback client (127.0.0.1, localhost, testclient).
       - Prevents unauthorized remote access in unauthenticated deployments.
    """
    admin_key = settings.ADMIN_API_KEY.strip() if settings.ADMIN_API_KEY else ""

    if admin_key:
        provided_key = None
        if header_key:
            provided_key = header_key.strip()
        elif bearer_creds:
            provided_key = bearer_creds.credentials.strip()

        if not provided_key or provided_key != admin_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Valid ADMIN_API_KEY required for this operation.",
                headers={"WWW-Authenticate": "Bearer or X-API-Key"}
            )
        return True

    # Fallback to local-only access check when ADMIN_API_KEY is not explicitly set
    client_host = request.client.host if request.client else ""
    if client_host not in LOCAL_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Forbidden: Remote access from '{client_host}' is blocked in local mode. "
                "Configure ADMIN_API_KEY in backend/.env to enable authenticated remote access."
            )
        )
    return True
