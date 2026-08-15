"""
Unit tests for TokenService in AnalystGPT Enterprise.
"""

from __future__ import annotations

import time

import pytest

from src.identity.exceptions import InvalidTokenError
from src.identity.models import User, UserRole, UserStatus
from src.identity.token_service import TokenService


@pytest.fixture
def sample_user() -> User:
    return User(
        id=42,
        username="token_analyst",
        email="token_analyst@enterprise.com",
        hashed_password="$pbkdf2$hash",
        role=UserRole.ANALYST,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def token_service() -> TokenService:
    return TokenService(
        secret_key="test-secret-key-for-testing-purposes-only",
        algorithm="HS256",
        expire_minutes=60,
    )


class TestTokenService:
    """Test suite for signed access token issuance and verification."""

    def test_create_and_verify_valid_token(
        self, token_service: TokenService, sample_user: User
    ) -> None:
        token = token_service.create_access_token(sample_user)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

        claims = token_service.verify_access_token(token)
        assert claims["sub"] == "42"
        assert claims["username"] == "token_analyst"
        assert claims["email"] == "token_analyst@enterprise.com"
        assert claims["role"] == "ANALYST"
        assert claims["type"] == "access"
        assert "exp" in claims
        assert "iat" in claims
        assert claims["exp"] > claims["iat"]

    def test_custom_expiration_lifetime(
        self, token_service: TokenService, sample_user: User
    ) -> None:
        token = token_service.create_access_token(sample_user, expires_delta_seconds=300)
        claims = token_service.verify_access_token(token)
        assert claims["exp"] - claims["iat"] == 300

    def test_expired_token_rejected(
        self, token_service: TokenService, sample_user: User
    ) -> None:
        # Create token that expired 10 seconds ago
        token = token_service.create_access_token(sample_user, expires_delta_seconds=-10)
        with pytest.raises(InvalidTokenError, match="expired"):
            token_service.verify_access_token(token)

    def test_tampered_signature_rejected(
        self, token_service: TokenService, sample_user: User
    ) -> None:
        token = token_service.create_access_token(sample_user)
        header, payload, signature = token.split(".")
        tampered_token = f"{header}.{payload}.invalidsignature123"

        with pytest.raises(InvalidTokenError, match="signature verification failed"):
            token_service.verify_access_token(tampered_token)

    def test_tampered_payload_rejected(
        self, token_service: TokenService, sample_user: User
    ) -> None:
        token = token_service.create_access_token(sample_user)
        header, payload, signature = token.split(".")
        # Tamper payload by modifying one char
        tampered_payload = ("A" if payload[0] != "A" else "B") + payload[1:]
        tampered_token = f"{header}.{tampered_payload}.{signature}"

        with pytest.raises(InvalidTokenError):
            token_service.verify_access_token(tampered_token)

    def test_different_secret_key_fails_verification(
        self, sample_user: User
    ) -> None:
        service_a = TokenService(secret_key="secret-key-alpha", algorithm="HS256")
        service_b = TokenService(secret_key="secret-key-beta", algorithm="HS256")

        token_a = service_a.create_access_token(sample_user)
        with pytest.raises(InvalidTokenError, match="signature verification failed"):
            service_b.verify_access_token(token_a)

    def test_malformed_token_formats_rejected(
        self, token_service: TokenService
    ) -> None:
        for malformed in ["", "not.enough.parts.extra", "singlepart", "two.parts"]:
            with pytest.raises(InvalidTokenError):
                token_service.verify_access_token(malformed)

    def test_unsupported_algorithm_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unsupported token algorithm"):
            TokenService(algorithm="RS256")
