"""
app/main.py — FastAPI application factory.

Configuration:
  - CORS is open for local development; restrict origins in production.
  - Rate limiting via SlowAPI.
  - OpenAPI docs at /docs and /redoc (disable in production).
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.limiter import limiter
from app.routers import auth, register

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Verify grid invariant at startup
# ------------------------------------------------------------------ #
if not settings.grid_invariant_ok:
    raise RuntimeError(
        f"Grid invariant violated: {settings.grid_total_nodes} != "
        f"{settings.grid_real_nodes} + {settings.grid_ghost_nodes}"
    )

app = FastAPI(
    title="2D Grid Authentication System",
    version="1.0.0",
    description=(
        "A mobile authentication system that allows registered users to authenticate "
        "using a randomized two-dimensional grid. Designed to reduce the effectiveness "
        "of shoulder surfing, replay attacks, and repeated guessing."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — open for Android emulator and local dev; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PRODUCTION: replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(register.router)
app.include_router(auth.router)


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for readiness probes."""
    return {"status": "ok"}
