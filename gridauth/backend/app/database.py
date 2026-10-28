"""
app/database.py — SQLAlchemy engine and session factory.

Supports SQLite for development and PostgreSQL for production.
The repository layer uses the get_db dependency; nothing else touches
the engine directly.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# ------------------------------------------------------------------ #
# Engine
# SQLite-specific: enable WAL mode and foreign-key enforcement.
# PostgreSQL needs no extra pragmas.
# ------------------------------------------------------------------ #
_connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=False,  # set True to log SQL during debugging; never log in production
)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
