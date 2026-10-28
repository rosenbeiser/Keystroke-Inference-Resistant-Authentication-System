"""
app/repositories/session_repo.py — Data access for auth sessions and session tokens.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuthSession, SessionToken


class SessionRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Grid auth sessions (short-lived, single-use)
    # ------------------------------------------------------------------ #

    def create_auth_session(
        self,
        user_id: int,
        nonce: str,
        real_node_indices_json: str,
        node_count: int,
        expires_at: datetime,
    ) -> AuthSession:
        session = AuthSession(
            user_id=user_id,
            nonce=nonce,
            real_node_indices=real_node_indices_json,
            node_count=node_count,
            expires_at=expires_at,
            consumed=False,
        )
        self._db.add(session)
        self._db.flush()
        return session

    def get_auth_session_by_nonce(self, nonce: str) -> AuthSession | None:
        return self._db.query(AuthSession).filter(AuthSession.nonce == nonce).first()

    def consume_session_atomically(self, session: AuthSession) -> bool:
        """
        Mark session as consumed.  Returns False if already consumed.

        SQLite serializes all writes so this is atomic under SQLite.
        For PostgreSQL, add SELECT FOR UPDATE before this check.
        """
        if session.consumed:
            return False
        session.consumed = True
        self._db.flush()
        return True

    # ------------------------------------------------------------------ #
    # Long-lived session tokens (post-login)
    # ------------------------------------------------------------------ #

    def create_session_token(self, user_id: int) -> SessionToken:
        token_str = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(
            now.timestamp() + settings.auth_token_expiry_seconds, tz=timezone.utc
        )
        tok = SessionToken(user_id=user_id, token=token_str, expires_at=expires_at)
        self._db.add(tok)
        self._db.flush()
        return tok

    def get_session_token(self, token: str) -> SessionToken | None:
        return self._db.query(SessionToken).filter(SessionToken.token == token).first()

    def revoke_session_token(self, token: str) -> None:
        tok = self.get_session_token(token)
        if tok:
            tok.revoked = True
            self._db.flush()
