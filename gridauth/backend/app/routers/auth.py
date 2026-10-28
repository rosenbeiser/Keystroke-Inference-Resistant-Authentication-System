"""
app/routers/auth.py — Authentication endpoints: session, verify, logout, status.
"""


import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.schemas import (
    LogoutResponse,
    SessionRequest,
    SessionResponse,
    StatusResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.services.auth_service import AuthError, AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
bearer = HTTPBearer()


# ------------------------------------------------------------------ #
# POST /api/v1/auth/session
# ------------------------------------------------------------------ #

@router.post(
    "/session",
    response_model=SessionResponse,
    summary="Create a grid authentication session",
    responses={
        401: {"description": "Invalid credentials or account locked"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{settings.rate_limit_session}/minute")
async def create_session(
    request: Request,
    body: SessionRequest,
    db: Session = Depends(get_db),
) -> SessionResponse:
    svc = AuthService(db)
    try:
        payload = svc.create_auth_session(body.username)
    except AuthError as e:
        code = status.HTTP_423_LOCKED if e.locked else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=code, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during session creation")
        raise HTTPException(status_code=500, detail="Internal server error")

    return SessionResponse(
        nonce=payload["nonce"],
        expires_at=payload["expires_at"],
        nodes=payload["nodes"],
        node_count=payload["node_count"],
    )


# ------------------------------------------------------------------ #
# POST /api/v1/auth/verify
# ------------------------------------------------------------------ #

@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify ordered grid selections",
    responses={
        401: {"description": "Authentication failed"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{settings.rate_limit_verify}/minute")
async def verify_session(
    request: Request,
    body: VerifyRequest,
    db: Session = Depends(get_db),
) -> VerifyResponse:
    svc = AuthService(db)
    try:
        result = svc.verify_selections(body.nonce, body.selections)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during verification")
        raise HTTPException(status_code=500, detail="Internal server error")

    return VerifyResponse(
        success=result["success"],
        message=result["message"],
        session_token=result.get("session_token"),
        token_expires_at=result.get("token_expires_at"),
    )


# ------------------------------------------------------------------ #
# POST /api/v1/auth/logout
# ------------------------------------------------------------------ #

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoke authenticated session",
)
async def logout(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> LogoutResponse:
    svc = AuthService(db)
    svc.logout(credentials.credentials)
    return LogoutResponse(message="Logged out successfully.")


# ------------------------------------------------------------------ #
# GET /api/v1/auth/status
# ------------------------------------------------------------------ #

@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Check authenticated session status",
    responses={401: {"description": "Unauthorized"}},
)
async def auth_status(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> StatusResponse:
    svc = AuthService(db)
    user = svc.get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return StatusResponse(
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
    )
