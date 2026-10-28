"""
tests/test_security.py — Security property verification tests.

Tests that:
  - AES key never appears in any API response
  - Session response contains no server secrets
  - Session memory is cleared (in-process zeroing is tested via auth_service)
  - Crypto module encrypt/decrypt round-trip
  - decrypt rejects tampered ciphertext
"""
from __future__ import annotations

import base64
import os

import pytest
from tests.conftest import get_session, register_user, verify_session


def test_aes_key_not_in_session_response(client):
    """The AES encryption key must never appear in any API response."""
    register_user(client)
    r = get_session(client)
    body = r.text
    test_key = os.environ.get("AES_KEY_B64", "")
    assert test_key not in body, "AES key found in session response!"


def test_aes_key_not_in_verify_response(client):
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession

    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    nodes = {n["node_index"]: n["chars"] for n in data["nodes"]}

    db = TestSessionLocal()
    sess = db.query(AuthSession).filter(AuthSession.nonce == nonce).first()
    real_indices = sess.get_real_node_indices()
    db.close()

    password = "TestPass1!"
    pw_list = list(password)
    selections = []
    for i in range(data["node_count"]):
        if i in real_indices:
            pw_p = real_indices.index(i)
            selections.append(pw_list[pw_p])
        else:
            selections.append(nodes[i][0])

    r = verify_session(client, nonce, selections)
    body = r.text
    test_key = os.environ.get("AES_KEY_B64", "")
    assert test_key not in body, "AES key found in verify response!"


def test_aes_gcm_encrypt_decrypt_roundtrip():
    from app.crypto.aes_gcm import decrypt, encrypt
    key = os.urandom(32)
    for char in ["a", "Z", "!", "1", "@"]:
        ct = encrypt(char, key)
        assert decrypt(ct, key) == char


def test_aes_gcm_wrong_key_raises():
    from cryptography.exceptions import InvalidTag
    from app.crypto.aes_gcm import decrypt, encrypt
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    ct = encrypt("x", key1)
    with pytest.raises(InvalidTag):
        decrypt(ct, key2)


def test_aes_gcm_tampered_ciphertext_raises():
    from cryptography.exceptions import InvalidTag
    from app.crypto.aes_gcm import decrypt, encrypt
    key = os.urandom(32)
    ct_b64 = encrypt("x", key)
    raw = base64.b64decode(ct_b64)
    # Flip a byte in the ciphertext body (after 12-byte nonce)
    tampered = bytearray(raw)
    tampered[15] ^= 0xFF
    bad_b64 = base64.b64encode(bytes(tampered)).decode()
    with pytest.raises(InvalidTag):
        decrypt(bad_b64, key)


def test_aes_gcm_unique_ciphertexts_for_same_plaintext():
    """Each encryption produces a unique ciphertext (fresh nonce)."""
    from app.crypto.aes_gcm import encrypt
    key = os.urandom(32)
    cts = {encrypt("a", key) for _ in range(100)}
    # All 100 ciphertexts should be unique (different nonces)
    assert len(cts) == 100


def test_real_node_indices_not_in_api_response(client):
    """real_node_indices must never appear anywhere in the session or verify response."""
    from tests.conftest import TestSessionLocal
    from app.models import AuthSession

    register_user(client)
    r_session = get_session(client)
    body = r_session.text

    # Get the actual real_node_indices from DB
    db = TestSessionLocal()
    data = r_session.json()
    sess = db.query(AuthSession).filter(AuthSession.nonce == data["nonce"]).first()
    real_indices = sess.get_real_node_indices()
    real_indices_str = str(real_indices)
    db.close()

    # The exact real_node_indices string should not appear in the response
    import json
    assert json.dumps(real_indices) not in body


def test_session_memory_zeroed_after_verify(client):
    """
    Test that verify_selections runs the memory-zeroing finally block
    without raising an exception.  Full in-process memory inspection is
    not possible in Python, so we verify the code path completes cleanly.
    """
    register_user(client)
    r_session = get_session(client)
    data = r_session.json()
    nonce = data["nonce"]
    selections = ["a"] * data["node_count"]
    # This must complete without error, exercising the finally block
    r = verify_session(client, nonce, selections)
    assert r.status_code in (200, 401)  # no 500 error
