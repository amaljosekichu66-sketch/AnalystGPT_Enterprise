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
import re
import time
import uuid
from typing import Any, TypeGuard

from src.core import config
from src.identity.exceptions import InvalidTokenError
from src.identity.models import User

_B64URL_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data_str: str) -> bytes:
    """
    Decode an unpadded URL-safe base64 segment, accepting only its canonical form.

    Padding or non-alphabet characters are refused (I1): `token + "=="` used to
    verify as the same token.
    """
    if not data_str or not _B64URL_SEGMENT.fullmatch(data_str) or len(data_str) % 4 == 1:
        raise ValueError("Non-canonical base64url segment.")
    decoded = base64.urlsafe_b64decode((data_str + "=" * (-len(data_str) % 4)).encode("ascii"))
    if _b64url_encode(decoded) != data_str:
        raise ValueError("Non-canonical base64url segment.")
    return decoded


#: Tolerance for iat/nbf against this server's clock (P3-05).
CLOCK_SKEW_SECONDS = 60


def _is_int(value: object) -> TypeGuard[int]:
    """A JSON integer claim; bool is an int subclass in Python and is refused."""
    return isinstance(value, int) and not isinstance(value, bool)


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
        # Building from configuration re-checks the key, so nothing can sign
        # with an unsafe key even if it bypassed the API startup check.
        self._secret_key = (secret_key if secret_key is not None else config.require_auth_secret_key()).encode("utf-8")
        self._algorithm = (algorithm if algorithm is not None else config.AUTH_ALGORITHM).upper()
        self._expire_seconds = (
            expire_minutes if expire_minutes is not None else config.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        ) * 60

        self._max_lifetime_seconds = int(config.AUTH_TOKEN_MAX_LIFETIME_MINUTES) * 60

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
        # Hard upper bound on lifetime (I2), whatever the configuration says.
        ttl = min(ttl, self._max_lifetime_seconds)
        exp = now + ttl

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        # `jti` makes every token unique - two logins in the same second used
        # to produce the identical token, so revoking one revoked both (and a
        # user who logged out and back in within that second was locked out).
        # It is also the key revocation is recorded under. `iss` / `aud` bind
        # the token to this service.
        payload: dict[str, Any] = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "iat": now,
            "exp": exp,
            "jti": uuid.uuid4().hex,
            "ver": user.token_version,
            "iss": config.AUTH_TOKEN_ISSUER,
            "aud": config.AUTH_TOKEN_AUDIENCE,
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

        # A token is base64url text. Anything else is malformed - reject it as
        # a 401 before `.encode("ascii")` raises a raw UnicodeEncodeError (400).
        if not token.isascii():
            raise InvalidTokenError("Malformed authentication token format.")

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

        if not _is_int(payload["exp"]):
            raise InvalidTokenError("Token expiration claim is not a number.")

        now = int(time.time())
        if payload["exp"] < now:
            raise InvalidTokenError("Authentication token has expired.")

        issued_at = payload.get("iat")
        if not _is_int(issued_at) or payload["exp"] - issued_at > self._max_lifetime_seconds:
            raise InvalidTokenError("Token lifetime exceeds the allowed maximum.")

        # P3-05: a token issued in the future, or not yet valid, is refused
        # (allowing CLOCK_SKEW_SECONDS for clocks that disagree slightly).
        if issued_at > now + CLOCK_SKEW_SECONDS:
            raise InvalidTokenError("Token issued in the future.")

        not_before = payload.get("nbf")
        if not_before is not None and (not _is_int(not_before) or not_before > now + CLOCK_SKEW_SECONDS):
            raise InvalidTokenError("Token is not yet valid.")

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type.")

        if "sub" not in payload:
            raise InvalidTokenError("Token missing subject identifier.")

        if not isinstance(payload.get("jti"), str) or not payload["jti"]:
            raise InvalidTokenError("Token missing unique identifier.")

        if payload.get("iss") != config.AUTH_TOKEN_ISSUER:
            raise InvalidTokenError("Token issuer is not accepted.")

        if payload.get("aud") != config.AUTH_TOKEN_AUDIENCE:
            raise InvalidTokenError("Token audience is not accepted.")

        return payload
