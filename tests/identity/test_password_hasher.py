"""
Tests for cryptographic password hasher.
"""

from __future__ import annotations

import pytest

from src.identity.password_hasher import PBKDF2PasswordHasher


class TestPBKDF2PasswordHasher:
    """Test PBKDF2-HMAC-SHA256 password hasher implementation."""

    def test_hash_format(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)
        hashed = hasher.hash("TestPassword123!")

        assert hashed.startswith("$pbkdf2-sha256$1000$")
        parts = hashed.split("$")
        assert len(parts) == 5  # empty, algorithm, iterations, salt, hash

    def test_verify_correct_password(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)
        password = "EnterpriseSecurePassword!987"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)
        hashed = hasher.hash("CorrectPassword")

        assert hasher.verify("WrongPassword", hashed) is False

    def test_unique_salts_produce_distinct_hashes(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)
        password = "SamePasswordAcrossUsers"

        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)

        assert hash1 != hash2
        assert hasher.verify(password, hash1) is True
        assert hasher.verify(password, hash2) is True

    def test_empty_password_rejected(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hasher.hash("")

    def test_verify_empty_or_malformed_hashes(self) -> None:
        hasher = PBKDF2PasswordHasher(iterations=1000)

        assert hasher.verify("password", "") is False
        assert hasher.verify("", "some_hash") is False
        assert hasher.verify("password", "invalid_prefix_hash") is False
        assert hasher.verify("password", "$pbkdf2-sha256$not_enough_parts") is False
