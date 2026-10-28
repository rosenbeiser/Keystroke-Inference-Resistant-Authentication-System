"""
tests/conftest.py — Shared test fixtures.

Uses an in-memory SQLite database so tests are isolated and fast.
The AES key is set to a fixed test value — NEVER use this key in production.
"""
from __future__ import annotations

import base64
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Set test env vars BEFORE importing app modules
TEST_AES_KEY = base64.b64encode(b"test_key_32bytes_test_key_32byt!").decode()
os.environ["AES_KEY_B64"] = TEST_AES_KEY
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SESSION_EXPIRY_SECONDS"] = "300"

from app.database import Base, get_db  # noqa: E402
from app.main import app, limiter  # noqa: E402
from app.models import *  # noqa: F401, F403, E402 — register all models

# Disable rate limiting during automated test runs
limiter.enabled = False

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    """Create and tear down the schema for each test."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(setup_db):
    """FastAPI test client with database override."""
    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Helper: register a test user via the API
def register_user(client, username="testuser", password="TestPass1!"):
    return client.post("/api/v1/register", json={"username": username, "password": password})


def get_session(client, username="testuser"):
    return client.post("/api/v1/auth/session", json={"username": username})


def verify_session(client, nonce, selections):
    return client.post("/api/v1/auth/verify", json={"nonce": nonce, "selections": selections})
