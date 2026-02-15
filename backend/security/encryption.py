"""
Synapsis Security — Encryption at Rest
=======================================

AES-256-GCM field-level encryption for sensitive data stored in SQLite.
Key is derived from a user-supplied passphrase via PBKDF2 (100 000 rounds).

No external dependencies — uses only Python ``cryptography`` stdlib-adjacent
package (already used by many pip deps) or falls back to a ``Fernet``-based
scheme if ``cryptography`` is missing.

Usage::

    from backend.security.encryption import get_encryptor

    enc = get_encryptor()          # reads key from SYNAPSIS_ENCRYPTION_KEY env
    ciphertext = enc.encrypt("sensitive data")
    plaintext  = enc.decrypt(ciphertext)

Key management:
  - Set ``SYNAPSIS_ENCRYPTION_KEY`` env var (min 16 chars).
  - If unset, encryption is **disabled** (passthrough mode) with a warning.
  - The key never leaves the local machine.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KEY_ENV = "SYNAPSIS_ENCRYPTION_KEY"
_PBKDF2_ITERATIONS = 100_000
_SALT_LEN = 16
_NONCE_LEN = 12       # AES-GCM standard
_TAG_LEN = 16         # GCM auth tag


# ---------------------------------------------------------------------------
# AES-GCM implementation (via `cryptography` package)
# ---------------------------------------------------------------------------

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 → 32-byte key."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )


class _AESGCMEncryptor:
    """AES-256-GCM using the `cryptography` library."""

    def __init__(self, passphrase: str) -> None:
        self._passphrase = passphrase
        # Validate the passphrase has some strength
        if len(passphrase) < 16:
            logger.warning("security.weak_encryption_key",
                           msg="Encryption key should be ≥16 characters")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt → base64 string (salt + nonce + ciphertext + tag)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        salt = secrets.token_bytes(_SALT_LEN)
        key = _derive_key(self._passphrase, salt)
        nonce = secrets.token_bytes(_NONCE_LEN)

        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Pack: salt (16) + nonce (12) + ciphertext+tag
        blob = salt + nonce + ct
        return base64.urlsafe_b64encode(blob).decode("ascii")

    def decrypt(self, token: str) -> str:
        """Decrypt a base64 token → plaintext string."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        blob = base64.urlsafe_b64decode(token.encode("ascii"))
        salt = blob[:_SALT_LEN]
        nonce = blob[_SALT_LEN : _SALT_LEN + _NONCE_LEN]
        ct = blob[_SALT_LEN + _NONCE_LEN :]

        key = _derive_key(self._passphrase, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ct, None)
        return plaintext.decode("utf-8")


# ---------------------------------------------------------------------------
# Fallback: HMAC-based simple encryption (no external deps)
# ---------------------------------------------------------------------------

class _FernetFallbackEncryptor:
    """Fallback XOR + HMAC-SHA256 when `cryptography` is not installed.

    This is NOT as secure as AES-GCM but provides basic obfuscation so
    data is not stored in plaintext.
    """

    def __init__(self, passphrase: str) -> None:
        self._key = hashlib.sha256(passphrase.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", self._key, salt, 10_000)
        data = plaintext.encode("utf-8")
        encrypted = bytes(d ^ derived[i % 32] for i, d in enumerate(data))
        mac = hmac.new(derived, encrypted, hashlib.sha256).digest()
        blob = salt + mac + encrypted
        return base64.urlsafe_b64encode(blob).decode("ascii")

    def decrypt(self, token: str) -> str:
        blob = base64.urlsafe_b64decode(token.encode("ascii"))
        salt = blob[:16]
        mac = blob[16:48]
        encrypted = blob[48:]
        derived = hashlib.pbkdf2_hmac("sha256", self._key, salt, 10_000)
        expected_mac = hmac.new(derived, encrypted, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Decryption failed: integrity check failed (wrong key?)")
        plaintext = bytes(d ^ derived[i % 32] for i, d in enumerate(encrypted))
        return plaintext.decode("utf-8")


# ---------------------------------------------------------------------------
# Passthrough (encryption disabled)
# ---------------------------------------------------------------------------

class _NoOpEncryptor:
    """When no key is configured — data passes through unencrypted."""

    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, token: str) -> str:
        return token


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class FieldEncryptor:
    """
    Unified interface for field-level encryption.

    Automatically picks the best available backend:
      1. AES-256-GCM (if ``cryptography`` is installed)
      2. HMAC+XOR fallback
      3. No-op passthrough (if no key configured)
    """

    def __init__(self, passphrase: Optional[str] = None) -> None:
        key = passphrase or os.environ.get(_KEY_ENV, "")

        if not key:
            logger.warning(
                "security.encryption_disabled",
                msg=f"Set {_KEY_ENV} env var to enable encryption at rest",
            )
            self._backend = _NoOpEncryptor()
            self.enabled = False
            return

        self.enabled = True
        try:
            # Test if cryptography is available
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
            self._backend = _AESGCMEncryptor(key)
            logger.info("security.encryption_enabled", backend="AES-256-GCM")
        except ImportError:
            self._backend = _FernetFallbackEncryptor(key)
            logger.info("security.encryption_enabled", backend="HMAC-XOR-fallback")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string field."""
        if not plaintext:
            return plaintext
        return self._backend.encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string field."""
        if not ciphertext:
            return ciphertext
        return self._backend.decrypt(ciphertext)

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specific fields in a dictionary (in-place copy)."""
        result = dict(data)
        for f in fields:
            if f in result and isinstance(result[f], str) and result[f]:
                result[f] = self.encrypt(result[f])
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Decrypt specific fields in a dictionary (in-place copy)."""
        result = dict(data)
        for f in fields:
            if f in result and isinstance(result[f], str) and result[f]:
                try:
                    result[f] = self.decrypt(result[f])
                except Exception:
                    pass  # field may not be encrypted (migration)
        return result


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_encryptor: Optional[FieldEncryptor] = None


def get_encryptor() -> FieldEncryptor:
    """Get or create the global encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = FieldEncryptor()
    return _encryptor
