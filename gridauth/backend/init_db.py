#!/usr/bin/env python
"""
init_db.py — Initialize the database schema.

Run this once before starting the backend:
    python init_db.py

For PostgreSQL, set DATABASE_URL in .env first.
This script is idempotent — safe to run multiple times.
"""
from __future__ import annotations

import sys

from app.config import settings
from app.database import Base, engine
from app.models import (  # noqa: F401 — imports register models with Base metadata
    AuditEvent,
    AuthSession,
    LockoutState,
    PasswordCharacter,
    PasswordHash,
    SessionToken,
    User,
)


def init() -> None:
    print(f"Initializing database: {settings.database_url}")
    Base.metadata.create_all(bind=engine)
    print("Schema created successfully.")
    print("\nAll tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    try:
        init()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
