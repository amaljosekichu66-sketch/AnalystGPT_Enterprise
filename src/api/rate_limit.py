"""
Per-client request rate limiting for unauthenticated endpoints (SEC-08).

`/api/auth/register` and `/api/auth/login` need no credentials, so without a
limit a single client could create accounts or guess passwords as fast as the
server answers. This is a sliding-window limiter keyed by client address
(`client_address`: the socket peer, or the forwarded address when the peer
is a trusted proxy such as the Streamlit frontend - M11).

Limits are "<requests>/<seconds>" strings from configuration and can be
switched off with `AUTH_RATE_LIMIT_ENABLED=false` (the test suite does, and
enables it explicitly where it is under test). State is per process.
"""

from __future__ import annotations

import ipaddress
import time
from collections import deque
from collections.abc import Callable
from functools import lru_cache
from threading import Lock

from fastapi import Request

from src.core import config


class RateLimitExceededError(Exception):
    """Raised when a client exceeds a rate limit. `retry_after` is in seconds."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Too many requests. Try again later.")
        self.retry_after = retry_after


def parse_limit(spec: str) -> tuple[int, int]:
    """Parse "<requests>/<seconds>" into (requests, seconds)."""
    count, _, window = spec.partition("/")
    return max(1, int(count)), max(1, int(window))


class SlidingWindowRateLimiter:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    def check(self, bucket: str, client: str, limit: int, window: int) -> None:
        now = self._clock()
        key = (bucket, client)
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - window:
                hits.popleft()
            if len(hits) >= limit:
                raise RateLimitExceededError(max(1, int(hits[0] + window - now + 0.999)))
            hits.append(now)
            if len(self._hits) > 10_000:
                self._evict(now, window)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _evict(self, now: float, window: int) -> None:
        for key in [k for k, v in self._hits.items() if not v or v[-1] <= now - window]:
            del self._hits[key]


limiter = SlidingWindowRateLimiter()


@lru_cache(maxsize=8)
def _trusted_networks(spec: str) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    return tuple(ipaddress.ip_network(part.strip(), strict=False) for part in spec.split(",") if part.strip())


def _is_trusted(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in _trusted_networks(config.TRUSTED_PROXY_IPS))


def client_address(request: Request) -> str:
    """
    The address a request is attributed to for rate limiting and lockout (M11).

    `X-Forwarded-For` is honoured only when the socket peer is listed in
    `TRUSTED_PROXY_IPS`; the chain is then walked from the right, skipping
    trusted hops, so a client cannot prepend a fake address. Anything
    malformed falls back to the socket peer.
    """
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded or not _is_trusted(peer):
        return peer
    for hop in reversed([part.strip() for part in forwarded.split(",")]):
        try:
            ipaddress.ip_address(hop)
        except ValueError:
            return peer
        if not _is_trusted(hop):
            return hop
    return peer


def rate_limit(bucket: str, spec_getter: Callable[[], str]) -> Callable:
    """FastAPI dependency: enforce the limit named by `spec_getter()` per client address."""

    async def dependency(request: Request) -> None:
        if not config.AUTH_RATE_LIMIT_ENABLED:
            return
        limit, window = parse_limit(spec_getter())
        limiter.check(bucket, client_address(request), limit, window)

    return dependency
