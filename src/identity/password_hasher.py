"""
Cryptographic password hashing implementation for AnalystGPT Enterprise.

Uses PBKDF2-HMAC-SHA256 with per-user cryptographic salts and constant-time
digest comparison adhering to OWASP/NIST guidelines.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

# ==========================================================
# Constants
# ==========================================================

_DEFAULT_ITERATIONS = 600_000
_SALT_BYTES = 16
_HASH_ALGORITHM = "sha256"
_PREFIX = "$pbkdf2-sha256$"


class PBKDF2PasswordHasher:
    """
    Standard PBKDF2-HMAC-SHA256 password hasher.
    """

    def __init__(
        self,
        iterations: int = _DEFAULT_ITERATIONS,
        salt_bytes: int = _SALT_BYTES,
    ) -> None:
        self._iterations = iterations
        self._salt_bytes = salt_bytes

    def hash(self, password: str) -> str:
        """
        Hash a plaintext password with a secure cryptographic salt.

        Returns
        -------
        str
            Encoded hash in format: `$pbkdf2-sha256$<iterations>$<salt_b64>$<hash_b64>`
        """
        if not password:
            raise ValueError("Password cannot be empty.")

        salt = secrets.token_bytes(self._salt_bytes)
        derived = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            self._iterations,
        )

        salt_b64 = base64.b64encode(salt).decode("ascii")
        hash_b64 = base64.b64encode(derived).decode("ascii")

        return f"{_PREFIX}{self._iterations}${salt_b64}${hash_b64}"

    def verify(self, password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against an encoded hash.

        Uses constant-time comparison to protect against timing attacks.
        """
        if not password or not hashed_password:
            return False

        if not hashed_password.startswith(_PREFIX):
            return False

        try:
            parts = hashed_password[len(_PREFIX) :].split("$")
            if len(parts) != 3:
                return False

            iterations_str, salt_b64, hash_b64 = parts
            iterations = int(iterations_str)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected_hash = base64.b64decode(hash_b64.encode("ascii"))

            derived = hashlib.pbkdf2_hmac(
                _HASH_ALGORITHM,
                password.encode("utf-8"),
                salt,
                iterations,
            )

            return hmac.compare_digest(derived, expected_hash)

        except Exception:
            return False
