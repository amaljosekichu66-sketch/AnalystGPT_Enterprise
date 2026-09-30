"""
Request body size limit for every API route (M3, L14).

The upload route checked `Content-Length` only when the header was present;
a chunked request skipped it, and `request.form()` spooled the whole body to
disk before any byte was counted. JSON endpoints had no limit at all.

This ASGI middleware counts body bytes as they arrive and stops the request
with 413 as soon as the route's limit is passed, so nothing larger is ever
buffered. The upload route gets the configured upload size (plus multipart
framing); every other route gets `MAX_REQUEST_BODY_KB`.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core import config

#: Multipart boundaries and part headers around the file itself.
MULTIPART_OVERHEAD_BYTES = 64 * 1024

#: (method, path) pairs that carry a dataset upload.
UPLOAD_ROUTES = frozenset({("POST", "/api/datasets")})


class RequestBodyTooLargeError(HTTPException):
    """
    Raised from `receive()` once the body passes the limit.

    An `HTTPException` on purpose: FastAPI turns any other error raised while
    reading a JSON body into a 400, but re-raises HTTP exceptions as they are.
    """

    def __init__(self, limit_bytes: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Request body exceeds the {limit_bytes:,}-byte limit for this endpoint.",
        )


def body_limit_bytes(method: str, path: str) -> int:
    """Largest body accepted for this route."""
    if (method.upper(), path.rstrip("/") or "/") in UPLOAD_ROUTES:
        return int(config.MAX_FILE_SIZE_MB) * 1024 * 1024 + MULTIPART_OVERHEAD_BYTES
    return int(config.MAX_REQUEST_BODY_KB) * 1024


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        limit = body_limit_bytes(scope.get("method", "GET"), scope.get("path", "/"))

        declared = dict(scope.get("headers") or []).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            await _reject(send, limit)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise RequestBodyTooLargeError(limit)
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except RequestBodyTooLargeError:
            # Normally rendered by the exception handlers; this covers a
            # body read outside a route (e.g. by another middleware).
            if not response_started:
                await _reject(send, limit)
            else:
                raise


async def _reject(send: Send, limit: int) -> None:
    body = (
        b'{"success":false,"message":"Request body too large.",'
        b'"error":"Request body exceeds the ' + f"{limit:,}".encode() + b'-byte limit for this endpoint."}'
    )
    await send(
        {
            "type": "http.response.start",
            "status": status.HTTP_413_CONTENT_TOO_LARGE,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})
