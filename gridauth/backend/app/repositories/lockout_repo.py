"""
app/repositories/lockout_repo.py — Data access for persistent lockout state.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import LockoutState


class LockoutRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_or_create(self, user_id: int) -> LockoutState:
        state = self._db.query(LockoutState).filter(LockoutState.user_id == user_id).first()
        if not state:
            state = LockoutState(user_id=user_id)
            self._db.add(state)
            self._db.flush()
        return state

    def increment_failure(self, user_id: int) -> LockoutState:
        state = self.get_or_create(user_id)
        state.failure_count += 1
        self._db.flush()
        return state

    def set_locked_until(self, user_id: int, until: datetime) -> None:
        state = self.get_or_create(user_id)
        current = state.locked_until
        if current is not None and current.tzinfo is None and until.tzinfo is not None:
            current = current.replace(tzinfo=until.tzinfo)
        elif current is not None and current.tzinfo is not None and until.tzinfo is None:
            until = until.replace(tzinfo=current.tzinfo)
        # Only extend; never shorten an existing lockout to a shorter one.
        if current is None or until > current:
            state.locked_until = until
        self._db.flush()

    def set_alert_threshold(self, user_id: int, threshold: int) -> None:
        state = self.get_or_create(user_id)
        state.last_alert_threshold = threshold
        self._db.flush()

    def reset_on_success(self, user_id: int) -> None:
        state = self.get_or_create(user_id)
        state.failure_count = 0
        state.locked_until = None
        state.last_alert_threshold = 0
        self._db.flush()
