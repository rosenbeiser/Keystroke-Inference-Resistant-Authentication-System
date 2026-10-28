"""
app/models.py — SQLAlchemy ORM models matching the database schema.

All tables are defined here.  Run init_db.py to create them.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    password_hash: Mapped["PasswordHash"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    password_chars: Mapped[list["PasswordCharacter"]] = relationship(back_populates="user", cascade="all, delete-orphan", order_by="PasswordCharacter.char_index")
    lockout: Mapped["LockoutState"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    session_tokens: Mapped[list["SessionToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    auth_sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PasswordHash(Base):
    __tablename__ = "password_hashes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="password_hash")


class PasswordCharacter(Base):
    """
    Stores each password character encrypted with AES-256-GCM.

    ciphertext is stored as base64(nonce || ciphertext || tag).
    The char_index preserves the original password character ordering
    so that per-position grid nodes can be constructed at session time.
    """
    __tablename__ = "password_characters"
    __table_args__ = (UniqueConstraint("user_id", "char_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    char_index: Mapped[int] = mapped_column(Integer, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="password_chars")


class AuthSession(Base):
    """
    Short-lived grid authentication session.

    real_node_indices is stored as a JSON array string and NEVER sent to clients.
    After nonce consumption the row stays for audit purposes but is marked consumed=True.
    """
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    real_node_indices: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="auth_sessions")

    def get_real_node_indices(self) -> list[int]:
        return json.loads(self.real_node_indices)


class LockoutState(Base):
    __tablename__ = "lockout_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_alert_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="lockout")


class SessionToken(Base):
    """Long-lived token issued after successful authentication (FR-07)."""
    __tablename__ = "session_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="session_tokens")


class AuditEvent(Base):
    """
    Append-only audit log.  Never store credentials, selections, or keys here.
    """
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="audit_events")
