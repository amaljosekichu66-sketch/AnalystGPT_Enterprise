"""
A small LRU mapping with a time-to-live (L10).

The application kept one full `PipelineResult` per run in plain dicts that
were never evicted, so memory grew with every pipeline execution. This is a
drop-in for those dicts: at most `max_entries` items, each forgotten
`ttl_seconds` after it was last written. Not thread-safe on its own; the
callers already hold `Application._cache_lock`.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class BoundedTTLCache(Generic[K, V]):
    def __init__(self, max_entries: int, ttl_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._max_entries = max(1, int(max_entries))
        self._ttl = float(ttl_seconds)
        self._clock = clock
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()

    def __setitem__(self, key: K, value: V) -> None:
        self._items.pop(key, None)
        self._items[key] = (self._clock(), value)
        self._expire()
        while len(self._items) > self._max_entries:
            self._items.popitem(last=False)

    def get(self, key: K, default: V | None = None) -> V | None:
        self._expire()
        item = self._items.get(key)
        return default if item is None else item[1]

    def pop(self, key: K, default: V | None = None) -> V | None:
        item = self._items.pop(key, None)
        return default if item is None else item[1]

    def __contains__(self, key: object) -> bool:
        self._expire()
        return key in self._items

    def __delitem__(self, key: K) -> None:
        del self._items[key]

    def __len__(self) -> int:
        self._expire()
        return len(self._items)

    def __iter__(self) -> Iterator[K]:
        self._expire()
        return iter(list(self._items))

    def items(self) -> list[tuple[K, V]]:
        """Oldest first, like insertion order in a dict."""
        self._expire()
        return [(key, value) for key, (_, value) in self._items.items()]

    def _expire(self) -> None:
        cutoff = self._clock() - self._ttl
        while self._items:
            key, (written, _) = next(iter(self._items.items()))
            if written >= cutoff:
                break
            del self._items[key]
