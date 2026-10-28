"""
tests/test_auth_verify.py — Verification and ordering enforcement tests.

Critical test: selections in the wrong order must fail even if
the correct characters are all present.
"""
from __future__ import annotations

import pytest
from tests.conftest import get_session, register_user, verify_session


def _do_correct_selections(client, username="testuser", password="TestPass1!"):
    """
    Simulate a legitimate user completing the grid.

    Strategy: for each node, we know its chars.  We select the
    first character (arbitrary).  The server knows which nodes are real
    and what the password characters are; this helper submits a selection
    array and returns the response plus what we submitted.
    """
    r_session = get_session(client, username)
    assert r_session.status_code == 200, r_session.text
    data = r_session.json()
    nonce = data["nonce"]
    nodes = data["nodes"]
    # Sort by node_index ascending (order of activation)
    nodes_sorted = sorted(nodes, key=lambda n: n["node_index"])
    # For a legitimate user: at real nodes they will naturally select the
    # correct password char (since it's always present in the K options).
    # We can't know which nodes are real from the client side, so for testing
    # we use the service directly.
    return nonce, nodes_sorted


def test_verify_with_all_first_chars(client):
    """
    Submit the first char of each node as the selection.
    This will fail for a real test since we don't control which chars are correct,
    but the endpoint should respond without server error.
    """
    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    selections = [node["chars"][0] for node in sorted(data["nodes"], key=lambda n: n["node_index"])]
    r = verify_session(client, nonce, selections)
    # Result is either success or failure — no 500 error
    assert r.status_code in (200,)
    assert "success" in r.json()


def test_verify_correct_login_e2e(client):
    """
    End-to-end test using the service layer to build correct selections.
    We bypass the client blindness by using the DB directly.
    """
    from app.services.auth_service import AuthService
    from app.database import get_db
    from tests.conftest import TestSessionLocal

    password = "TestPass1!"
    register_user(client, password=password)

    # Get session via API
    r_session = get_session(client)
    assert r_session.status_code == 200
    data = r_session.json()
    nonce = data["nonce"]
    nodes = {n["node_index"]: n["chars"] for n in data["nodes"]}

    # Read real_node_indices from DB
    db = TestSessionLocal()
    from app.models import AuthSession
    sess = db.query(AuthSession).filter(AuthSession.nonce == nonce).first()
    real_indices = sess.get_real_node_indices()
    db.close()

    # Build correct selection array: at real nodes pick the correct password char
    # At ghost nodes pick any char
    pw_list = list(password)
    selections = []
    pw_pos = 0
    for i in range(data["node_count"]):
        if i in real_indices:
            # This is a real node; find which password position it is
            pw_p = real_indices.index(i)
            selections.append(pw_list[pw_p])
        else:
            selections.append(nodes[i][0])  # ghost: pick any

    r = verify_session(client, nonce, selections)
    assert r.status_code == 200
    result = r.json()
    assert result["success"] is True
    assert "session_token" in result
    assert result["session_token"] is not None


def test_verify_wrong_password(client):
    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    # All wrong characters
    selections = ["Z"] * data["node_count"]
    r = verify_session(client, nonce, selections)
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_verify_ordering_enforced(client):
    """
    CRITICAL SECURITY TEST.

    Submit the correct password characters at the correct real node positions
    but in WRONG ORDER.  Verification must fail.

    This validates that the ordering requirement is enforced server-side.
    Dropping it would collapse ~73-bit entropy to ~53-bit.
    """
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession

    password = "ABcdefG1"
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
    # Build REVERSED password order at real nodes
    reversed_pw = list(reversed(pw_list))
    selections = []
    pw_pos = 0
    rev_pos = 0
    for i in range(data["node_count"]):
        if i in real_indices:
            pw_p = real_indices.index(i)
            # Use reversed char — may or may not be in the node's char set.
            # If the reversed char happens to be in the set, we deliberately
            # place it wrong-order; if not, it will also fail.
            # Either way, the correct-order sequence is not submitted.
            wrong_char = reversed_pw[rev_pos % len(reversed_pw)]
            rev_pos += 1
            selections.append(wrong_char)
        else:
            selections.append(nodes[i][0])

    r = verify_session(client, nonce, selections)
    # Unless reversed password == password (palindrome), this MUST fail
    if password != password[::-1]:
        assert r.json()["success"] is False, (
            "ORDERING NOT ENFORCED: reversed password sequence was accepted!"
        )


def test_verify_nonce_replay_rejected(client):
    """
    Submit the same nonce twice.  The second attempt must be rejected.
    """
    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    selections = ["a"] * data["node_count"]

    # First submission
    verify_session(client, nonce, selections)

    # Second submission with same nonce — MUST be rejected
    r2 = verify_session(client, nonce, selections)
    assert r2.status_code in (200, 401)
    if r2.status_code == 200:
        assert r2.json()["success"] is False


def test_verify_expired_nonce(client):
    """Test that an expired nonce is rejected."""
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession
    from datetime import datetime, timezone, timedelta

    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]

    # Manually expire the session
    db = TestSessionLocal()
    sess = db.query(AuthSession).filter(AuthSession.nonce == nonce).first()
    sess.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    db.close()

    selections = ["a"] * data["node_count"]
    r = verify_session(client, nonce, selections)
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        assert r.json()["success"] is False


def test_verify_wrong_selection_count(client):
    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    # Wrong number of selections
    r = verify_session(client, nonce, ["a"])
    # Either 401 unauthorized, 422 validation error, or 200 with success=False
    assert r.status_code in (200, 401, 422)
    if r.status_code == 200:
        assert r.json()["success"] is False


def test_verify_success_returns_session_token(client):
    """Successful auth must return a non-empty session token."""
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

    r = verify_session(client, nonce, selections)
    result = r.json()
    assert result["success"] is True
    assert result["session_token"]
    assert len(result["session_token"]) > 10
