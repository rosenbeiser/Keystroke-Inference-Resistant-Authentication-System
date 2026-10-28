"""
tests/test_nonce.py — Nonce lifecycle and replay protection tests.
"""
from __future__ import annotations

import pytest
from tests.conftest import get_session, register_user, verify_session


def test_nonce_is_unique_across_sessions(client):
    register_user(client)
    nonces = set()
    for _ in range(5):
        r = get_session(client)
        # Consume the nonce so next session can be created
        nonce = r.json()["nonce"]
        node_count = r.json()["node_count"]
        verify_session(client, nonce, ["a"] * node_count)
        nonces.add(nonce)
    assert len(nonces) == 5


def test_nonce_replay_rejected(client):
    register_user(client)
    r = get_session(client)
    data = r.json()
    nonce = data["nonce"]
    selections = ["a"] * data["node_count"]

    # First use
    r1 = verify_session(client, nonce, selections)

    # Replay — must be rejected
    r2 = verify_session(client, nonce, selections)
    assert r2.status_code in (200, 401)
    if r2.status_code == 200:
        assert r2.json()["success"] is False, "Nonce replay must not succeed"


def test_invalid_nonce_rejected(client):
    register_user(client)
    r = verify_session(client, "this-is-not-a-valid-nonce", ["a"] * 10)
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        assert r.json()["success"] is False


def test_nonce_not_reused_after_success(client):
    """
    After a successful authentication the nonce is consumed.
    Attempting to reuse it must fail.
    """
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession

    password = "TestPass1!"
    register_user(client, password=password)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    nodes = {n["node_index"]: n["chars"] for n in data["nodes"]}

    db = TestSessionLocal()
    sess = db.query(AuthSession).filter(AuthSession.nonce == nonce).first()
    real_indices = sess.get_real_node_indices()
    db.close()

    pw_list = list(password)
    selections = []
    for i in range(data["node_count"]):
        if i in real_indices:
            pw_p = real_indices.index(i)
            selections.append(pw_list[pw_p])
        else:
            selections.append(nodes[i][0])

    # Successful login
    r1 = verify_session(client, nonce, selections)
    assert r1.json()["success"] is True

    # Attempt replay
    r2 = verify_session(client, nonce, selections)
    assert r2.status_code in (200, 401)
    if r2.status_code == 200:
        assert r2.json()["success"] is False, "Nonce reuse after success must be rejected"
