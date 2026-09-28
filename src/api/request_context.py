"""
Per-request correlation id (SEC-11).

Error responses no longer carry raw exception text; they carry a request id
instead, and the full exception is logged server-side under the same id. A
caller-supplied `X-Request-ID` is honoured when it is a short token of safe
characters, otherwise a fresh id is generated. The id is echoed in the
`X-Request-ID` response header.

Implemented as a pure ASGI middleware (not `BaseHTTPMiddleware`) so the
context variable stays visible to Starlette's outermost 500 handler.
"""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"

_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return _request_id.get()


class RequestIdMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                supplied = value.decode("latin-1")
                break
        request_id = supplied if supplied and _SAFE_REQUEST_ID.match(supplied) else uuid.uuid4().hex
        _request_id.set(request_id)

        async def send_with_id(message):
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_id)
