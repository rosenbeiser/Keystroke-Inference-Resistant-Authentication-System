"""
app/routers/register.py — Registration endpoint.
"""


import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.schemas import RegisterRequest, RegisterResponse
from app.services.auth_service import AuthError, AuthService, RegistrationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["registration"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        400: {"description": "Validation failure"},
        409: {"description": "Username already taken"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(f"{settings.rate_limit_register}/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    svc = AuthService(db)
    try:
        svc.register_user(body.username, body.password)
    except RegistrationError as e:
        # Use 409 for duplicate — specific enough for UX, generic enough for security
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during registration")
        raise HTTPException(status_code=500, detail="Internal server error")
    return RegisterResponse(message="Registration successful.", username=body.username)
