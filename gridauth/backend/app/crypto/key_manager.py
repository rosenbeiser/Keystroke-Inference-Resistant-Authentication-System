"""
app/crypto/key_manager.py — Key management abstraction layer.

DEVELOPMENT: EnvVarKeyManager reads the AES key from an environment
variable.  This is NOT production-safe.

PRODUCTION: Replace EnvVarKeyManager with a cloud-provider KMS
implementation (e.g., AwsKmsKeyManager, AzureKeyVaultKeyManager).
The interface has a single method: load_key() -> bytes.
No other code needs to change.

Architecture note (from design doc):
    The AES-256-GCM key is stored outside the database as a development
    substitute for an HSM-backed key management system such as AWS CloudHSM
    or Azure Key Vault.  To migrate: implement AbstractKeyManager, configure
    the dependency injection below to use the new implementation, and remove
    the AES_KEY_B64 environment variable.
"""
from __future__ import annotations

import abc

from app.config import settings


class AbstractKeyManager(abc.ABC):
    """Interface that all KMS implementations must satisfy."""

    @abc.abstractmethod
    def load_key(self) -> bytes:
        """Return the 32-byte AES-256 encryption key.
        May raise RuntimeError on misconfiguration or KMS unavailability.
        """


class EnvVarKeyManager(AbstractKeyManager):
    """
    DEVELOPMENT ONLY.

    Reads the key from the AES_KEY_B64 environment variable decoded from
    base64.  The key never touches the database; it lives only in process
    memory during the request.

    To replace with a production KMS:
        1. Implement AbstractKeyManager.load_key() against your KMS SDK.
        2. Swap the binding below:  key_manager = YourKmsKeyManager()
        3. Remove AES_KEY_B64 from .env.
    """

    def load_key(self) -> bytes:
        return settings.get_aes_key_bytes()


# ------------------------------------------------------------------ #
# Dependency injection point.
# Change this single line to swap implementations.
# ------------------------------------------------------------------ #
key_manager: AbstractKeyManager = EnvVarKeyManager()
