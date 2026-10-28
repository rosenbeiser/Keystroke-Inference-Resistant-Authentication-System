"""
tests/test_lockout.py — Escalating lockout policy tests (FR-06).
"""
from __future__ import annotations

import pytest
from tests.conftest import get_session, register_user, verify_session


def _fail_n_times(client, n: int, username="testuser"):
    """Trigger n consecutive failed authentication attempts."""
    from datetime import datetime, timedelta, timezone
    from tests.conftest import TestSessionLocal
    from app.models import LockoutState, User

    for _ in range(n):
        # If currently locked from a previous threshold in this sequence,
        # simulate the lockout period having passed so the next batch of attempts can be tested
        db = TestSessionLocal()
        user = db.query(User).filter(User.username == username).first()
        if user:
            state = db.query(LockoutState).filter(LockoutState.user_id == user.id).first()
            if state and state.locked_until:
                state.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
                db.commit()
        db.close()

        r_session = get_session(client, username)
        assert r_session.status_code == 200, f"Session creation failed: {r_session.text}"
        data = r_session.json()
        # Submit all wrong chars
        selections = ["Z"] * data["node_count"]
        verify_session(client, data["nonce"], selections)


def test_lockout_after_5_failures(client):
    register_user(client)
    _fail_n_times(client, 5)
    r = get_session(client)
    assert r.status_code == 423  # HTTP 423 Locked


def test_lockout_after_10_failures(client):
    register_user(client)
    _fail_n_times(client, 10)
    r = get_session(client)
    assert r.status_code == 423


def test_lockout_after_15_failures(client):
    register_user(client)
    _fail_n_times(client, 15)
    r = get_session(client)
    assert r.status_code == 423


def test_no_lockout_before_5(client):
    register_user(client)
    _fail_n_times(client, 4)
    r = get_session(client)
    # Should still be able to create a session
    assert r.status_code == 200


def test_alert_fires_at_3_failures(client, caplog):
    """
    The logging alert adapter must fire exactly once at the 3-failure threshold
    and not again during the same lockout cycle.
    """
    import logging
    register_user(client)
    with caplog.at_level(logging.WARNING):
        _fail_n_times(client, 3)

    alert_logs = [r for r in caplog.records if "DEV ALERT ADAPTER" in r.message]
    assert len(alert_logs) >= 1, "Alert must fire at 3 failures"


def test_alert_does_not_fire_again_in_same_cycle(client, caplog):
    """
    Alert must fire only once per lockout cycle.  After 3 failures fire once;
    4th and 5th failures should NOT fire another alert.
    """
    import logging
    register_user(client)
    with caplog.at_level(logging.WARNING):
        _fail_n_times(client, 5)

    alert_logs = [r for r in caplog.records if "DEV ALERT ADAPTER" in r.message]
    # Should fire exactly once (at failure #3), not again at #4 or #5
    assert len(alert_logs) == 1, f"Expected 1 alert, got {len(alert_logs)}"


def test_lockout_persists_in_db(client):
    """
    Lockout state is persisted; simulated by checking DB directly.
    """
    from tests.conftest import TestSessionLocal
    from app.models import LockoutState, User

    register_user(client)
    _fail_n_times(client, 5)

    db = TestSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    state = db.query(LockoutState).filter(LockoutState.user_id == user.id).first()
    assert state is not None
    assert state.failure_count >= 5
    assert state.locked_until is not None
    db.close()


def test_lockout_reset_on_success(client):
    """
    After successful authentication, failure counter resets to 0.
    """
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession, LockoutState, User

    password = "TestPass1!"
    register_user(client, password=password)
    _fail_n_times(client, 2)  # Fewer than lockout threshold

    # Now do a successful login
    r_session = get_session(client)
    data = r_session.json()
    nodes = {n["node_index"]: n["chars"] for n in data["nodes"]}
    nonce = data["nonce"]

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

    verify_session(client, nonce, selections)

    # Check counter reset
    db = TestSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    state = db.query(LockoutState).filter(LockoutState.user_id == user.id).first()
    assert state.failure_count == 0
    assert state.locked_until is None
    db.close()
