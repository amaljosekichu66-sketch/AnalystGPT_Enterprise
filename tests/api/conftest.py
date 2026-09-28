"""
Shared configuration for the HTTP API test package.

Why this file exists
--------------------
`X-User-Id` / `X-User-Name` / `X-User-Role` are unauthenticated request
headers. Production refuses them (`config.AUTH_ALLOW_HEADER_IDENTITY` defaults
to False), because honouring them is a complete authentication bypass.

The RBAC tests in this package still need a cheap way to present an identity
without minting a signed token for every case, so the flag is enabled here -
and *only* here, for the duration of each test. Tests that assert the
production posture (`test_security_boundary.py`) monkeypatch it back to False
in their own body, which takes precedence because it is applied later.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def allow_header_identity_for_api_tests(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Enable development identity headers for this package's tests."""
    monkeypatch.setattr(
        "src.core.config.AUTH_ALLOW_HEADER_IDENTITY",
        True,
        raising=False,
    )
    yield
