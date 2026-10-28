"""
app/services/alert_service.py — Alert provider abstraction.

DEVELOPMENT: LoggingAlertAdapter prints to stdout/stderr.
It is clearly labeled as a development adapter and does NOT represent
a delivered alert to the user's secondary channel.

PRODUCTION: Replace LoggingAlertAdapter with a real delivery provider
(e.g., TwilioSmsProvider, FirebasePushProvider) that implements
AbstractAlertProvider.  Only the binding at the bottom of this file
needs to change — no other code is affected.

Alert deduplication is handled by LockoutService using the
last_alert_threshold field in the database.
"""
from __future__ import annotations

import abc
import logging

logger = logging.getLogger(__name__)


class AbstractAlertProvider(abc.ABC):
    """Interface for secondary-channel alert delivery."""

    @abc.abstractmethod
    def send_alert(self, username: str, failure_count: int, message: str) -> None:
        """
        Send a security alert to the user's registered secondary channel.

        Parameters
        ----------
        username : str
            The account identifier.
        failure_count : int
            The current consecutive failure count that triggered the alert.
        message : str
            A human-readable alert message.
        """


class LoggingAlertAdapter(AbstractAlertProvider):
    """
    DEVELOPMENT ONLY — NOT a real alert delivery mechanism.

    This adapter logs the alert to the application console.
    It serves as a clearly-labeled placeholder that satisfies the
    AbstractAlertProvider interface so the rest of the application
    compiles and tests pass.

    In production, replace this with a real provider that delivers
    the alert via SMS (e.g., Twilio), push notification (e.g., Firebase),
    or email (e.g., SendGrid).  The interface contract is:
        send_alert(username, failure_count, message) -> None
    """

    def send_alert(self, username: str, failure_count: int, message: str) -> None:
        # DEVELOPMENT ADAPTER — output goes to console log only.
        # This does NOT deliver an alert to the end user's secondary channel.
        logger.warning(
            "[DEV ALERT ADAPTER] Secondary channel alert (NOT DELIVERED): "
            "user=%s failures=%d message=%r",
            username,
            failure_count,
            message,
        )
        # In production, replace above with:
        # sms_client.send(to=user.phone_number, body=message)
        # or push_client.notify(device_token=user.device_token, body=message)


# ------------------------------------------------------------------ #
# Dependency injection point.
# Swap this line to change alert providers without touching other code.
# ------------------------------------------------------------------ #
alert_provider: AbstractAlertProvider = LoggingAlertAdapter()
