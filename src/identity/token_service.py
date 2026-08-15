"""
Cryptographic access token service for AnalystGPT Enterprise.

Implements stateless HMAC-SHA256 signed access tokens with standard claims,
expiration validation, and constant-time signature verification.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from src.core import config
from src.identity.exceptions import InvalidTokenError
from src.identity.models import User


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data_str: str) -> bytes:
    """Decode URL-safe base64 string with restored padding."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("ascii"))


class TokenService:
    """
    Service responsible for generating and validating cryptographically signed access tokens.
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        expire_minutes: int | None = None,
    ) -> None:
        self._secret_key = (secret_key if secret_key is not None else config.AUTH_SECRET_KEY).encode("utf-8")
        self._algorithm = (algorithm if algorithm is not None else config.AUTH_ALGORITHM).upper()
        self._expire_seconds = (
            expire_minutes if expire_minutes is not None else config.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        ) * 60

        if self._algorithm != "HS256":
            raise ValueError(f"Unsupported token algorithm: {self._algorithm}. Only HS256 is supported.")

    def create_access_token(
        self,
        user: User,
        expires_delta_seconds: int | None = None,
    ) -> str:
        """
        Generate a cryptographically signed access token for the given user.

        Parameters
        ----------
        user:
            Authenticated user entity.
        expires_delta_seconds:
            Optional custom expiration lifetime in seconds.

        Returns
        -------
        str
            Signed JWT string.
        """
        now = int(time.time())
        ttl = expires_delta_seconds if expires_delta_seconds is not None else self._expire_seconds
        exp = now + ttl

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        payload: dict[str, Any] = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "iat": now,
            "exp": exp,
        }

        header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
        payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        header_b64 = _b64url_encode(header_json)
        payload_b64 = _b64url_encode(payload_json)

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        signature = hmac.new(self._secret_key, signing_input, hashlib.sha256).digest()
        signature_b64 = _b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """
        Verify token signature, validity, and expiration, returning decoded claims.

        Parameters
        ----------
        token:
            Signed JWT string.

        Returns
        -------
        dict[str, Any]
            Verified payload claims.

        Raises
        ------
        InvalidTokenError
            If token is malformed, expired, tampered, or invalid.
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Authentication token is missing or invalid.")

        parts = token.strip().split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Malformed authentication token format.")

        header_b64, payload_b64, signature_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(self._secret_key, signing_input, hashlib.sha256).digest()

        try:
            provided_sig = _b64url_decode(signature_b64)
        except Exception as exc:
            raise InvalidTokenError("Invalid token signature encoding.") from exc

        if not hmac.compare_digest(expected_sig, provided_sig):
            raise InvalidTokenError("Token signature verification failed.")

        try:
            payload_bytes = _b64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            raise InvalidTokenError("Malformed token payload.") from exc

        # Validate standard claims
        if not isinstance(payload, dict):
            raise InvalidTokenError("Token payload must be a JSON object.")

        if "exp" not in payload:
            raise InvalidTokenError("Token missing expiration claim.")

        now = int(time.time())
        if payload["exp"] < now:
            raise InvalidTokenError("Authentication token has expired.")

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type.")

        if "sub" not in payload:
            raise InvalidTokenError("Token missing subject identifier.")

        return payload
