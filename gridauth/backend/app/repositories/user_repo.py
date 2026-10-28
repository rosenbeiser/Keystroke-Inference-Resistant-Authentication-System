"""
app/repositories/user_repo.py — Data access layer for users and password storage.

All database access goes through these functions.
No business logic lives here.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import PasswordCharacter, PasswordHash, User


class UserRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # User queries
    # ------------------------------------------------------------------ #

    def get_by_username(self, username: str) -> User | None:
        return self._db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self._db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str) -> User:
        user = User(username=username)
        self._db.add(user)
        self._db.flush()  # get id without committing
        return user

    # ------------------------------------------------------------------ #
    # Password hash
    # ------------------------------------------------------------------ #

    def set_password_hash(self, user_id: int, hash_str: str) -> None:
        existing = self._db.query(PasswordHash).filter(PasswordHash.user_id == user_id).first()
        if existing:
            existing.hash = hash_str
        else:
            self._db.add(PasswordHash(user_id=user_id, hash=hash_str))
        self._db.flush()

    def get_password_hash(self, user_id: int) -> PasswordHash | None:
        return self._db.query(PasswordHash).filter(PasswordHash.user_id == user_id).first()

    # ------------------------------------------------------------------ #
    # Encrypted password characters
    # ------------------------------------------------------------------ #

    def set_password_characters(self, user_id: int, encrypted_chars: list[str]) -> None:
        """Replace all stored characters for this user."""
        self._db.query(PasswordCharacter).filter(PasswordCharacter.user_id == user_id).delete()
        for i, ct in enumerate(encrypted_chars):
            self._db.add(PasswordCharacter(user_id=user_id, char_index=i, ciphertext=ct))
        self._db.flush()

    def get_password_characters(self, user_id: int) -> list[PasswordCharacter]:
        return (
            self._db.query(PasswordCharacter)
            .filter(PasswordCharacter.user_id == user_id)
            .order_by(PasswordCharacter.char_index)
            .all()
        )
