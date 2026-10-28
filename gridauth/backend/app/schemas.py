"""
app/schemas.py — Pydantic request and response schemas.

All schemas validate inputs rigorously. Secrets never appear
in response schemas. API documentation examples are sanitized.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ------------------------------------------------------------------ #
# Registration
# ------------------------------------------------------------------ #

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError(f"Password must contain {', '.join(errors)}")
        return v


class RegisterResponse(BaseModel):
    message: str
    username: str


# ------------------------------------------------------------------ #
# Grid session creation
# ------------------------------------------------------------------ #

class SessionRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)


class NodeResponse(BaseModel):
    """Single node in the returned grid.  No role or password info included."""
    node_index: int
    chars: list[str] = Field(..., min_length=1)


class SessionResponse(BaseModel):
    nonce: str
    expires_at: datetime
    nodes: list[NodeResponse]
    node_count: int


# ------------------------------------------------------------------ #
# Verify (authenticate)
# ------------------------------------------------------------------ #

class VerifyRequest(BaseModel):
    nonce: str = Field(..., min_length=1, max_length=256)
    selections: list[str] = Field(..., min_length=1, max_length=50)

    @field_validator("selections")
    @classmethod
    def selections_not_empty(cls, v: list[str]) -> list[str]:
        for s in v:
            if not s or len(s) != 1:
                raise ValueError("Each selection must be exactly one character")
        return v


class VerifyResponse(BaseModel):
    success: bool
    message: str
    session_token: str | None = None
    token_expires_at: datetime | None = None


# ------------------------------------------------------------------ #
# Logout
# ------------------------------------------------------------------ #

class LogoutResponse(BaseModel):
    message: str


# ------------------------------------------------------------------ #
# Auth status (protected endpoint)
# ------------------------------------------------------------------ #

class StatusResponse(BaseModel):
    username: str
    is_active: bool
    created_at: datetime


# ------------------------------------------------------------------ #
# Generic error
# ------------------------------------------------------------------ #

class ErrorResponse(BaseModel):
    detail: str
