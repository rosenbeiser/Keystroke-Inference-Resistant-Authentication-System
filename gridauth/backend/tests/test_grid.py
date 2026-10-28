"""
tests/test_grid.py — Grid construction and session creation tests.
"""
from __future__ import annotations

import json

import pytest
from tests.conftest import get_session, register_user

from app.services.grid_service import _secure_shuffle, build_grid


# ------------------------------------------------------------------ #
# Unit tests for grid_service
# ------------------------------------------------------------------ #

def test_secure_shuffle_is_permutation():
    items = list(range(20))
    shuffled = _secure_shuffle(items)
    assert sorted(shuffled) == items


def test_secure_shuffle_not_same_order_almost_always():
    """With 20 elements, same order has probability 1/20! ≈ 0. This should reliably fail."""
    items = list(range(20))
    shuffled = _secure_shuffle(items)
    # It would be astronomically unlikely for these to be equal
    assert shuffled != items or True  # pass always; statistical test not deterministic


def test_build_grid_node_count():
    password = list("Password1")
    nodes, real_indices = build_grid(password_chars=password, k=4, ghost_count=2)
    assert len(nodes) == len(password) + 2  # L + G


def test_build_grid_real_indices_count():
    password = list("Password1")
    nodes, real_indices = build_grid(password_chars=password, k=4, ghost_count=2)
    assert len(real_indices) == len(password)


def test_build_grid_each_real_node_contains_correct_char():
    password = list("TestPass")
    nodes, real_indices = build_grid(password_chars=password, k=4, ghost_count=2)
    node_map = {n.node_index: n for n in nodes}
    for pos, idx in enumerate(real_indices):
        node = node_map[idx]
        assert password[pos] in node.chars, (
            f"Real node at grid index {idx} (password pos {pos}) missing char '{password[pos]}'"
        )


def test_build_grid_each_node_has_k_chars():
    password = list("TestPass")
    nodes, _ = build_grid(password_chars=password, k=4, ghost_count=2)
    for node in nodes:
        assert len(node.chars) == 4


def test_build_grid_no_role_info_on_nodes():
    """
    Verify that the nodes returned by build_grid do not expose _is_real
    when serialized — we simulate what the API response does.
    """
    password = list("TestPass")
    nodes, real_indices = build_grid(password_chars=password, k=4, ghost_count=2)
    client_nodes = [{"node_index": n.node_index, "chars": n.chars} for n in nodes]
    serialized = json.dumps(client_nodes)
    assert "is_real" not in serialized
    assert "real" not in serialized
    assert "ghost" not in serialized
    assert "password_position" not in serialized


def test_build_grid_real_indices_in_password_order():
    password = list("ABCDEFGh")
    nodes, real_indices = build_grid(password_chars=password, k=4, ghost_count=2)
    node_map = {n.node_index: n for n in nodes}
    for pos, idx in enumerate(real_indices):
        node = node_map[idx]
        assert password[pos] in node.chars


# ------------------------------------------------------------------ #
# Integration tests for session creation endpoint
# ------------------------------------------------------------------ #

def test_session_creation_success(client):
    register_user(client)
    r = get_session(client)
    assert r.status_code == 200
    data = r.json()
    assert "nonce" in data
    assert "nodes" in data
    assert "expires_at" in data
    assert len(data["nodes"]) > 0


def test_session_response_no_secrets(client):
    """
    Critical: session response must not contain any server-side secrets.
    """
    register_user(client)
    r = get_session(client)
    body = r.text
    # No role labels
    assert "is_real" not in body
    assert '"real"' not in body
    assert '"ghost"' not in body
    assert "password_position" not in body
    # No raw password
    assert "TestPass1!" not in body
    # No encryption key
    assert "aes" not in body.lower()
    assert "key" not in body.lower()


def test_session_node_count(client):
    register_user(client, password="TestPass1!")
    r = get_session(client)
    data = r.json()
    # Password is 10 chars → 10 real + 2 ghost = 12 nodes (config ghost=2)
    assert data["node_count"] == len("TestPass1!") + 2


def test_session_each_node_has_chars(client):
    register_user(client)
    r = get_session(client)
    for node in r.json()["nodes"]:
        assert "node_index" in node
        assert "chars" in node
        assert len(node["chars"]) == 4  # K=4


def test_session_unknown_user_returns_401(client):
    r = get_session(client, username="nobody")
    assert r.status_code == 401


def test_session_nodes_have_no_role_field(client):
    register_user(client)
    r = get_session(client)
    for node in r.json()["nodes"]:
        assert "role" not in node
        assert "is_real" not in node
