"""
app/config.py — Application configuration loaded from environment variables.

All values have defaults suitable for local development.
Never put real secrets in this file — use a .env file or shell exports.
"""
from __future__ import annotations

import base64
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "sqlite:///./gridauth.db"

    # ------------------------------------------------------------------ #
    # Encryption key  (32 bytes, base64-encoded)
    # Production: replace EnvVarKeyManager with an HSM-backed implementation.
    # ------------------------------------------------------------------ #
    aes_key_b64: str = ""

    # ------------------------------------------------------------------ #
    # Grid configuration
    # ------------------------------------------------------------------ #
    grid_total_nodes: int = 10
    grid_real_nodes: int = 8
    grid_ghost_nodes: int = 2
    grid_chars_per_node: int = 4

    # ------------------------------------------------------------------ #
    # Session / token lifetimes
    # ------------------------------------------------------------------ #
    session_expiry_seconds: int = 300     # grid session (short-lived)
    auth_token_expiry_seconds: int = 3600  # post-login token

    # ------------------------------------------------------------------ #
    # Password policy
    # ------------------------------------------------------------------ #
    password_min_length: int = 8
    password_max_length: int = 128

    # ------------------------------------------------------------------ #
    # Rate limiting
    # ------------------------------------------------------------------ #
    rate_limit_register: int = 5    # per minute per IP
    rate_limit_session: int = 10
    rate_limit_verify: int = 10

    def get_aes_key_bytes(self) -> bytes:
        """Decode and validate the AES key.  Raises on misconfiguration."""
        if not self.aes_key_b64:
            raise RuntimeError(
                "AES_KEY_B64 environment variable is not set. "
                "Generate one with: python -c \"import secrets,base64; "
                "print(base64.b64encode(secrets.token_bytes(32)).decode())\""
            )
        key = base64.b64decode(self.aes_key_b64)
        if len(key) != 32:
            raise RuntimeError(
                f"AES_KEY_B64 must decode to exactly 32 bytes (got {len(key)})"
            )
        return key

    @property
    def grid_invariant_ok(self) -> bool:
        return self.grid_total_nodes == self.grid_real_nodes + self.grid_ghost_nodes


settings = Settings()
