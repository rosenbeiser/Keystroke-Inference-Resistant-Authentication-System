"""
tests/test_registration.py — Registration endpoint tests.
"""
from __future__ import annotations

import pytest
from tests.conftest import register_user


def test_register_success(client):
    r = register_user(client)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "testuser"
    assert "message" in data


def test_register_duplicate_username(client):
    register_user(client)
    r = register_user(client)
    assert r.status_code == 409


def test_register_short_password(client):
    r = client.post("/api/v1/register", json={"username": "alice", "password": "Sh1!"})
    assert r.status_code == 422


def test_register_no_uppercase(client):
    r = client.post("/api/v1/register", json={"username": "alice", "password": "testpass1!"})
    assert r.status_code == 422


def test_register_no_digit(client):
    r = client.post("/api/v1/register", json={"username": "alice", "password": "TestPass!!"})
    assert r.status_code == 422


def test_register_no_lowercase(client):
    r = client.post("/api/v1/register", json={"username": "alice", "password": "TESTPASS1!"})
    assert r.status_code == 422


def test_register_username_too_short(client):
    r = client.post("/api/v1/register", json={"username": "ab", "password": "TestPass1!"})
    assert r.status_code == 422


def test_register_username_invalid_chars(client):
    r = client.post("/api/v1/register", json={"username": "alice smith", "password": "TestPass1!"})
    assert r.status_code == 422


def test_register_response_no_password(client):
    """Registration response must never contain the password or its hash."""
    r = register_user(client)
    body = r.text
    assert "TestPass1!" not in body
    assert "hash" not in body
    assert "password" not in body.lower() or "password" not in r.json()
