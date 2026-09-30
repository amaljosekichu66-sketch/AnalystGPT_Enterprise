"""
Security response headers for every API response (L14).

The API returned no hardening headers at all. It serves JSON and file
downloads only, so the policy is strict: nothing may be framed, sniffed,
scripted or referred. The interactive docs (enabled outside production) need
scripts and styles from their CDN, so they get a CSP of their own.

HSTS is sent only when `API_HSTS_ENABLED` is set: it must come from the
TLS-terminating proxy's hostname, and a wrong value locks browsers out.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core import config

_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_DOCS_CSP = (
    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'"
)
_DOCS_PATHS = ("/docs", "/redoc")


def _headers_for(path: str) -> list[tuple[bytes, bytes]]:
    csp = _DOCS_CSP if path.startswith(_DOCS_PATHS) else _API_CSP
    headers = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"no-referrer"),
        (b"content-security-policy", csp.encode()),
        (b"cross-origin-opener-policy", b"same-origin"),
        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    ]
    if config.API_HSTS_ENABLED:
        headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
    return headers


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        extra = _headers_for(scope.get("path", "/"))

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {name.lower() for name, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (name, value) for name, value in extra if name not in existing
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)
