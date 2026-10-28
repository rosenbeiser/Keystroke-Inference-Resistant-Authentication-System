"""
app/services/lockout_service.py — Escalating lockout policy (FR-06).

Exact thresholds (from spec):
  3 failures  → send secondary-channel alert (once per lockout cycle)
  5 failures  → lock for 10 minutes
  10 failures → lock for 20 minutes
  15 failures → lock for 24 hours
  Success     → reset failure counter to 0

Lockout durations are enforced using server-side timestamps stored
in the database so restarting the server cannot bypass them.

A longer lockout ALWAYS replaces a shorter one (the repository
enforces this invariant in set_locked_until).

Alert deduplication: last_alert_threshold tracks the highest failure
count for which an alert has already been sent in this lockout cycle.
An alert fires only when failure_count crosses a new threshold.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import LockoutState
from app.repositories.lockout_repo import LockoutRepository
from app.services.alert_service import alert_provider

logger = logging.getLogger(__name__)

# Thresholds (spec-mandated, do not change without updating documentation)
_ALERT_THRESHOLD = 3
_LOCK_THRESHOLDS: dict[int, timedelta] = {
    5: timedelta(minutes=10),
    10: timedelta(minutes=20),
    15: timedelta(hours=24),
}


class LockoutService:

    def __init__(self, db: Session) -> None:
        self._repo = LockoutRepository(db)

    def check_lockout(self, user_id: int) -> tuple[bool, str]:
        """
        Returns (is_locked: bool, message: str).
        Caller should refuse to proceed if is_locked is True.
        """
        state = self._repo.get_or_create(user_id)
        if state.locked_until:
            now = datetime.now(timezone.utc)
            locked_until = state.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds())
                return True, f"Account locked. Try again in {remaining} seconds."
        return False, ""

    def record_failure(self, user_id: int, username: str) -> None:
        """
        Increment failure counter and apply lockout/alert policy.
        Must be called after every failed authentication attempt.
        """
        state = self._repo.increment_failure(user_id)
        count = state.failure_count

        # Alert — fires only once per threshold per lockout cycle
        if count >= _ALERT_THRESHOLD and state.last_alert_threshold < _ALERT_THRESHOLD:
            self._send_alert(username, count)
            self._repo.set_alert_threshold(user_id, _ALERT_THRESHOLD)

        # Lockout — apply the most severe applicable threshold
        now = datetime.now(timezone.utc)
        for threshold in sorted(_LOCK_THRESHOLDS.keys(), reverse=True):
            if count >= threshold:
                locked_until = now + _LOCK_THRESHOLDS[threshold]
                self._repo.set_locked_until(user_id, locked_until)
                logger.warning(
                    "Account locked: user_id=%d count=%d until=%s",
                    user_id, count, locked_until.isoformat(),
                )
                break

    def record_success(self, user_id: int) -> None:
        """Reset failure counter after successful authentication."""
        self._repo.reset_on_success(user_id)

    def _send_alert(self, username: str, failure_count: int) -> None:
        msg = (
            f"Security alert: {failure_count} consecutive failed login attempts "
            f"detected for account '{username}'. If this was not you, "
            "please secure your account immediately."
        )
        alert_provider.send_alert(username=username, failure_count=failure_count, message=msg)
