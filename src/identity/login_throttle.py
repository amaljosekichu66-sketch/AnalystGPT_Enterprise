"""
Progressive per-account login lockout (SEC-08).

Fifteen wrong passwords followed by the right one used to log straight in.
Now, after `AUTH_LOGIN_MAX_FAILURES` consecutive failures for one identifier,
every attempt - even with the correct password - is refused until the lockout
expires. Each further failure doubles the lockout, up to a cap. A successful
login resets the counter.

Identifiers are throttled whether or not the account exists, so the lockout
does not reveal which usernames are registered. State is per process; with
several API workers each keeps its own counters.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

from src.core import config


@dataclass
class _State:
    failures: int = 0
    locked_until: float = 0.0
    last_failure: float = 0.0


class LoginThrottle:
    #: Failure counters for identifiers idle this long are forgotten.
    IDLE_RESET_SECONDS = 3600

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._states: dict[str, _State] = {}
        self._lock = Lock()

    @staticmethod
    def _key(identifier: str) -> str:
        return identifier.strip().lower()

    def retry_after(self, identifier: str) -> int:
        """Seconds until `identifier` may try again (0 = not locked)."""
        now = self._clock()
        with self._lock:
            state = self._states.get(self._key(identifier))
            if state is None or state.locked_until <= now:
                return 0
            return max(1, int(state.locked_until - now + 0.999))

    def record_failure(self, identifier: str) -> int:
        """Count a failed attempt; return the lockout (seconds) it triggered, or 0."""
        now = self._clock()
        threshold = max(1, int(config.AUTH_LOGIN_MAX_FAILURES))
        with self._lock:
            self._prune(now)
            state = self._states.setdefault(self._key(identifier), _State())
            state.failures += 1
            state.last_failure = now
            if state.failures < threshold:
                return 0
            extra = state.failures - threshold
            lockout = min(
                int(config.AUTH_LOGIN_LOCKOUT_BASE_SECONDS) * (2 ** min(extra, 16)),
                int(config.AUTH_LOGIN_LOCKOUT_MAX_SECONDS),
            )
            state.locked_until = now + lockout
            return lockout

    def record_success(self, identifier: str) -> None:
        with self._lock:
            self._states.pop(self._key(identifier), None)

    def reset(self) -> None:
        with self._lock:
            self._states.clear()

    def _prune(self, now: float) -> None:
        stale = [
            key
            for key, state in self._states.items()
            if state.locked_until <= now and now - state.last_failure > self.IDLE_RESET_SECONDS
        ]
        for key in stale:
            del self._states[key]
