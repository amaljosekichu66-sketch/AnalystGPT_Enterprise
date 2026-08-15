"""
Token revocation tracking service for AnalystGPT Enterprise.

Provides in-memory thread-safe tracking of revoked access tokens upon logout.
"""

from __future__ import annotations

from threading import Lock


class TokenRevocationService:
    """
    Registry for invalidated/revoked access tokens.
    """

    def __init__(self) -> None:
        self._revoked_tokens: set[str] = set()
        self._lock = Lock()

    def revoke_token(self, token: str) -> None:
        """
        Mark an access token as revoked.
        """
        if not token:
            return

        with self._lock:
            self._revoked_tokens.add(token.strip())

    def is_revoked(self, token: str) -> bool:
        """
        Check if an access token has been revoked.
        """
        if not token:
            return False

        with self._lock:
            return token.strip() in self._revoked_tokens
