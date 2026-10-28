"""
app/crypto/aes_gcm.py — AES-256-GCM authenticated encryption helpers.

Ciphertext wire format:  base64( nonce[12] || ciphertext || tag[16] )

The 12-byte nonce is generated fresh for every encryption call using
os.urandom, giving 96-bit nonce uniqueness.  With a 32-byte (256-bit)
key this provides 128-bit authentication tag strength.

The GCM tag is embedded by cryptography library's AESGCM — it appends
the tag automatically, so decryption only needs to split nonce from the rest.
"""
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_LEN = 12  # bytes; NIST recommended for GCM


def encrypt(plaintext: str, key: bytes) -> str:
    """
    Encrypt a single password character (or any short string) under key.

    Returns a base64-encoded string safe for database storage.
    The plaintext is encoded as UTF-8 before encryption.
    The key must be exactly 32 bytes.
    """
    nonce = os.urandom(_NONCE_LEN)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct_with_tag).decode("ascii")


def decrypt(ciphertext_b64: str, key: bytes) -> str:
    """
    Decrypt a base64-encoded ciphertext produced by encrypt().

    Returns the original plaintext string.
    Raises cryptography.exceptions.InvalidTag if the tag is invalid
    (wrong key, tampered data, or wrong nonce).
    """
    raw = base64.b64decode(ciphertext_b64)
    nonce = raw[:_NONCE_LEN]
    ct_with_tag = raw[_NONCE_LEN:]
    aesgcm = AESGCM(key)
    plaintext_bytes = aesgcm.decrypt(nonce, ct_with_tag, None)
    return plaintext_bytes.decode("utf-8")
