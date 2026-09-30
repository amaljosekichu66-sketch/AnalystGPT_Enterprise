"""
Login lockout (SEC-08; reworked for M12, L5 and I3).

Three counters, each forgotten after `IDLE_RESET_SECONDS` without a failure:

- account + source: after `AUTH_LOGIN_MAX_FAILURES` consecutive failures for
  one account from one client address, that address is refused for that
  account - even with the right password - for
  `AUTH_LOGIN_LOCKOUT_BASE_SECONDS`, doubling up to
  `AUTH_LOGIN_LOCKOUT_MAX_SECONDS`. This is the brute-force brake.
- account, every source: after `AUTH_LOGIN_ACCOUNT_MAX_FAILURES` failures a
  short, non-escalating back-off (`AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS`).
  The lockout used to be keyed on the identifier alone, so anyone could keep
  an account locked with one request every 15 minutes (M12). Now only a
  distributed attack reaches this counter, and it cannot hold the owner out
  for long.
- source, every account: after `AUTH_LOGIN_SOURCE_MAX_FAILURES` failures the
  address is locked progressively for every account. One common password
  tried across many accounts never tripped a per-account counter (L5).

Refused attempts are not counted, so a locked-out source cannot feed the
account-wide counter.

"Account" is `user:<id>` when the identifier resolves to a user, so username
and email share one counter, and the normalised identifier otherwise. Unknown
identifiers are throttled the same way, so a lockout does not reveal whether
an account exists.

State lives in a pluggable store: in memory by default, and the
`login_failures` table in the API (`DatabaseThrottleStore`), so lockouts
survive restarts and are shared by workers (I3). Concurrent failures on
several workers may occasionally lose an increment; the counters are a
brake, not an exact tally.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

from src.core import config

PAIR = "pair"
ACCOUNT = "account"
SOURCE = "source"


@dataclass
class ThrottleState:
    failures: int = 0
    locked_until: float = 0.0
    last_failure: float = 0.0


class ThrottleStore(Protocol):
    def get(self, scope: str, key: str) -> ThrottleState | None: ...

    def put(self, scope: str, key: str, state: ThrottleState) -> None: ...

    def delete(self, scope: str, key: str) -> None: ...

    def delete_account(self, account: str) -> None: ...

    def prune(self, now: float, idle_seconds: float) -> None: ...

    def clear(self) -> None: ...


class InMemoryThrottleStore:
    def __init__(self) -> None:
        self._states: dict[tuple[str, str], ThrottleState] = {}

    def get(self, scope: str, key: str) -> ThrottleState | None:
        state = self._states.get((scope, key))
        return None if state is None else ThrottleState(state.failures, state.locked_until, state.last_failure)

    def put(self, scope: str, key: str, state: ThrottleState) -> None:
        self._states[(scope, key)] = ThrottleState(state.failures, state.locked_until, state.last_failure)

    def delete(self, scope: str, key: str) -> None:
        self._states.pop((scope, key), None)

    def delete_account(self, account: str) -> None:
        prefix = pair_key(account, "")
        for scope, key in list(self._states):
            if (scope == ACCOUNT and key == account) or (scope == PAIR and key.startswith(prefix)):
                del self._states[(scope, key)]

    def prune(self, now: float, idle_seconds: float) -> None:
        for item, state in list(self._states.items()):
            if state.locked_until <= now and now - state.last_failure > idle_seconds:
                del self._states[item]

    def clear(self) -> None:
        self._states.clear()


def pair_key(account: str, source: str) -> str:
    return f"{account}|{source}"


class LoginThrottle:
    #: Failure counters idle this long are forgotten.
    IDLE_RESET_SECONDS = 3600

    #: Prune stale rows once every this many recorded failures.
    PRUNE_EVERY = 100

    def __init__(self, clock=time.time, store: ThrottleStore | None = None) -> None:
        self._clock = clock
        self._store: ThrottleStore = store if store is not None else InMemoryThrottleStore()
        self._lock = Lock()
        self._failures_since_prune = 0

    @staticmethod
    def normalise(identifier: str) -> str:
        return identifier.strip().lower()

    def retry_after(self, account: str, source: str = "") -> int:
        """Seconds until `account` may be tried again from `source` (0 = not locked)."""
        now = self._clock()
        with self._lock:
            locked_until = max(
                (state.locked_until for state in self._states_for(account, source, now) if state is not None),
                default=0.0,
            )
        if locked_until <= now:
            return 0
        return max(1, int(locked_until - now + 0.999))

    def record_failure(self, account: str, source: str = "") -> int:
        """Count a failed attempt; return the per-source lockout (seconds) it triggered, or 0."""
        now = self._clock()
        with self._lock:
            self._maybe_prune(now)
            pair, whole_account, whole_source = self._states_for(account, source, now)

            pair = self._bump(pair, now)
            lockout = self._progressive(pair, int(config.AUTH_LOGIN_MAX_FAILURES), now)
            self._store.put(PAIR, pair_key(account, source), pair)

            whole_account = self._bump(whole_account, now)
            if whole_account.failures >= max(1, int(config.AUTH_LOGIN_ACCOUNT_MAX_FAILURES)):
                whole_account.locked_until = now + int(config.AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS)
            self._store.put(ACCOUNT, account, whole_account)

            if source:
                whole_source = self._bump(whole_source, now)
                self._progressive(whole_source, int(config.AUTH_LOGIN_SOURCE_MAX_FAILURES), now)
                self._store.put(SOURCE, source, whole_source)

            return lockout

    def record_success(self, account: str, source: str = "") -> None:
        """Clear the account's counters for this source. The per-source spray counter is kept."""
        with self._lock:
            self._store.delete(PAIR, pair_key(account, source))
            self._store.delete(ACCOUNT, account)

    def unlock(self, account: str) -> None:
        """Clear every counter for `account`, from every source (admin unlock)."""
        with self._lock:
            self._store.delete_account(account)

    def reset(self) -> None:
        with self._lock:
            self._store.clear()

    # ------------------------------------------------------------------

    def _states_for(self, account: str, source: str, now: float) -> list[ThrottleState | None]:
        states = [
            self._store.get(PAIR, pair_key(account, source)),
            self._store.get(ACCOUNT, account),
            self._store.get(SOURCE, source) if source else None,
        ]
        return [self._fresh(state, now) for state in states]

    def _fresh(self, state: ThrottleState | None, now: float) -> ThrottleState | None:
        if state is None:
            return None
        if state.locked_until <= now and now - state.last_failure > self.IDLE_RESET_SECONDS:
            return None
        return state

    @staticmethod
    def _bump(state: ThrottleState | None, now: float) -> ThrottleState:
        state = state if state is not None else ThrottleState()
        state.failures += 1
        state.last_failure = now
        return state

    @staticmethod
    def _progressive(state: ThrottleState, threshold: int, now: float) -> int:
        threshold = max(1, threshold)
        if state.failures < threshold:
            return 0
        extra = state.failures - threshold
        lockout = min(
            int(config.AUTH_LOGIN_LOCKOUT_BASE_SECONDS) * (2 ** min(extra, 16)),
            int(config.AUTH_LOGIN_LOCKOUT_MAX_SECONDS),
        )
        state.locked_until = now + lockout
        return lockout

    def _maybe_prune(self, now: float) -> None:
        self._failures_since_prune += 1
        if self._failures_since_prune >= self.PRUNE_EVERY:
            self._failures_since_prune = 0
            self._store.prune(now, self.IDLE_RESET_SECONDS)
