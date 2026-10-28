"""
app/services/auth_service.py — Core authentication business logic.

Implements:
  - User registration (FR-01)
  - Grid session creation (FR-03, FR-05)
  - Session verification with ordering enforcement (FR-04, FR-05)
  - Post-login session token management (FR-07)
"""
from __future__ import annotations

import gc
import json
import logging
import secrets
from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session

from app.config import settings
from app.crypto.aes_gcm import decrypt, encrypt
from app.crypto.key_manager import key_manager
from app.repositories.lockout_repo import LockoutRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.services.grid_service import build_grid
from app.services.lockout_service import LockoutService

logger = logging.getLogger(__name__)

_ph = PasswordHasher(
    time_cost=2,       # iterations
    memory_cost=65536, # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


class RegistrationError(Exception):
    pass


class AuthError(Exception):
    def __init__(self, message: str, locked: bool = False) -> None:
        super().__init__(message)
        self.locked = locked


class AuthService:

    def __init__(self, db: Session) -> None:
        self._db = db
        self._user_repo = UserRepository(db)
        self._session_repo = SessionRepository(db)
        self._lockout_svc = LockoutService(db)

    # ------------------------------------------------------------------ #
    # FR-01: Registration
    # ------------------------------------------------------------------ #

    def register_user(self, username: str, password: str) -> None:
        """
        Register a new user.

        Steps:
          1. Validate username availability.
          2. Hash password with Argon2id.
          3. Encrypt each character individually with AES-256-GCM.
          4. Persist user, hash, and encrypted characters atomically.
          5. Zero the plaintext password from local variables immediately.

        Raises RegistrationError on validation failure or duplicate username.
        Never logs the password, key, or encrypted ciphertext content.
        """
        if self._user_repo.get_by_username(username):
            raise RegistrationError("Registration failed.")  # generic to avoid enumeration

        # Step 2: Hash
        password_hash = _ph.hash(password)

        # Step 3: Encrypt each character separately
        aes_key = key_manager.load_key()
        encrypted_chars: list[str] = []
        try:
            for char in password:
                encrypted_chars.append(encrypt(char, aes_key))
        finally:
            # Zero the key bytes from memory as soon as possible
            aes_key = b"\x00" * len(aes_key)
            del aes_key
            gc.collect()

        # Step 4: Persist atomically
        user = self._user_repo.create_user(username)
        self._user_repo.set_password_hash(user.id, password_hash)
        self._user_repo.set_password_characters(user.id, encrypted_chars)
        self._db.commit()

        logger.info("User registered: username=%s", username)

    # ------------------------------------------------------------------ #
    # FR-03 / FR-05: Grid session creation
    # ------------------------------------------------------------------ #

    def create_auth_session(self, username: str) -> dict:
        """
        Create a new grid authentication session.

        Returns a dict with the client-safe session payload:
          { nonce, expires_at, nodes: [{node_index, chars}], node_count }

        The real_node_indices are stored server-side only and never returned.
        Raises AuthError if account is locked or not found.
        """
        # Use generic "not found" path to avoid account enumeration
        user = self._user_repo.get_by_username(username)
        if not user or not user.is_active:
            # Simulate work to avoid timing-based enumeration
            _ph.hash("dummy_password_to_avoid_timing_leak")
            raise AuthError("Invalid credentials.")

        # Check lockout before proceeding
        is_locked, lock_msg = self._lockout_svc.check_lockout(user.id)
        if is_locked:
            raise AuthError(lock_msg, locked=True)

        # Decrypt password characters
        aes_key = key_manager.load_key()
        password_chars: list[str] = []
        try:
            char_records = self._user_repo.get_password_characters(user.id)
            for record in char_records:
                password_chars.append(decrypt(record.ciphertext, aes_key))
        finally:
            aes_key = b"\x00" * len(aes_key)
            del aes_key
            gc.collect()

        if not password_chars:
            raise AuthError("Invalid credentials.")

        # Build randomized grid
        nodes, real_node_indices = build_grid(
            password_chars=password_chars,
            k=settings.grid_chars_per_node,
            ghost_count=settings.grid_ghost_nodes,
        )

        # Zero decrypted password characters immediately after grid construction
        password_chars = ["\x00"] * len(password_chars)
        del password_chars
        gc.collect()

        # Create session record
        nonce = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(
            now.timestamp() + settings.session_expiry_seconds, tz=timezone.utc
        )

        auth_session = self._session_repo.create_auth_session(
            user_id=user.id,
            nonce=nonce,
            real_node_indices_json=json.dumps(real_node_indices),
            node_count=len(nodes),
            expires_at=expires_at,
        )
        self._db.commit()

        # Build client-safe response — NO roles, NO real_node_indices
        client_nodes = [
            {"node_index": n.node_index, "chars": n.chars}
            for n in sorted(nodes, key=lambda x: x.node_index)
        ]

        return {
            "nonce": nonce,
            "expires_at": expires_at,
            "nodes": client_nodes,
            "node_count": len(nodes),
        }

    # ------------------------------------------------------------------ #
    # FR-04 / FR-05: Verification
    # ------------------------------------------------------------------ #

    def verify_selections(self, nonce: str, selections: list[str]) -> dict:
        """
        Verify ordered selections against stored password.

        Critical security property:
          Ordering is enforced on the SERVER.  The server extracts the
          sub-sequence of selections at real_node_indices (in password order)
          and compares them character-by-character against the stored password.
          Wrong order = verification failure.

        Steps:
          1. Validate nonce existence, expiry, and consumed state.
          2. Atomically mark nonce consumed (prevents replay).
          3. Validate selection count matches node count.
          4. Decrypt stored password characters.
          5. Extract selections at real_node_indices IN ORDER.
          6. Compare extracted sequence vs password sequence.
          7. Update lockout state.
          8. Issue session token on success.
          9. Zero all in-memory session data.

        Returns { success, message, session_token?, token_expires_at? }
        Always returns a generic failure message; does not reveal which
        position or character failed.
        """
        auth_session = self._session_repo.get_auth_session_by_nonce(nonce)
        now = datetime.now(timezone.utc)

        session_data: dict | None = None
        password_chars: list[str] | None = None
        aes_key: bytes | None = None

        try:
            # Step 1: Validate nonce
            if auth_session is None:
                raise AuthError("Authentication failed.")

            expires_at = auth_session.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                raise AuthError("Session expired.")

            if auth_session.consumed:
                raise AuthError("Authentication failed.")  # replay

            # Step 2: Atomic consumption
            consumed = self._session_repo.consume_session_atomically(auth_session)
            if not consumed:
                raise AuthError("Authentication failed.")  # race condition

            # Step 3: Validate selection count
            if len(selections) != auth_session.node_count:
                self._lockout_svc.record_failure(auth_session.user_id, auth_session.user.username)
                self._db.commit()
                raise AuthError("Authentication failed.")

            # Step 4: Decrypt password
            aes_key = key_manager.load_key()
            char_records = self._user_repo.get_password_characters(auth_session.user_id)
            password_chars = [decrypt(r.ciphertext, aes_key) for r in char_records]

            # Step 5: Extract selections at real positions (IN PASSWORD ORDER)
            real_indices = auth_session.get_real_node_indices()  # list[int], password-ordered
            extracted = [selections[i] for i in real_indices]

            # Step 6: Constant-time comparison (prevent timing oracle)
            password_str = "".join(password_chars)
            extracted_str = "".join(extracted)
            match = secrets.compare_digest(password_str, extracted_str)

            # Step 7: Update lockout
            user = auth_session.user
            if match:
                self._lockout_svc.record_success(user.id)
            else:
                self._lockout_svc.record_failure(user.id, user.username)

            self._db.commit()

            if not match:
                return {"success": False, "message": "Authentication failed."}

            # Step 8: Issue session token
            session_token = self._session_repo.create_session_token(user.id)
            self._db.commit()

            session_data = {
                "success": True,
                "message": "Authentication successful.",
                "session_token": session_token.token,
                "token_expires_at": session_token.expires_at,
            }
            return session_data

        finally:
            # Step 9: Zero in-memory session data
            if password_chars is not None:
                for i in range(len(password_chars)):
                    password_chars[i] = "\x00"
                del password_chars
            if aes_key is not None:
                aes_key = b"\x00" * len(aes_key)
                del aes_key
            gc.collect()

    # ------------------------------------------------------------------ #
    # FR-07: Logout
    # ------------------------------------------------------------------ #

    def logout(self, token: str) -> None:
        self._session_repo.revoke_session_token(token)
        self._db.commit()

    def get_user_by_token(self, token: str):
        tok = self._session_repo.get_session_token(token)
        if not tok or tok.revoked:
            return None
        now = datetime.now(timezone.utc)
        expires_at = tok.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            return None
        return tok.user
