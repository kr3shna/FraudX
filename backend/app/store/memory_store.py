from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.models.response import ForensicResult


class MemoryStore:
    """
    TTL-based in-memory result cache.

    Stores the last N forensic results keyed by session token.
    Oldest entries are evicted when the store reaches capacity.
    Expired entries (older than TTL) are lazily evicted on every read/write.

    Thread safety: not required — single-worker uvicorn process assumption.
    """

    def __init__(self, ttl_seconds: int, max_items: int) -> None:
        # OrderedDict preserves insertion order for LRU-style eviction.
        self._store: OrderedDict[str, tuple[datetime, ForensicResult]] = OrderedDict()
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max = max_items

    def set(self, key: str, value: ForensicResult) -> None:
        """Store a result. Evicts expired entries first, then oldest if at capacity."""
        self._evict_expired()
        if key in self._store:
            # Refresh existing key — move to end so it's treated as newest.
            del self._store[key]
        elif len(self._store) >= self._max:
            # Capacity reached — remove the oldest entry (first item).
            self._store.popitem(last=False)
        self._store[key] = (datetime.now(tz=timezone.utc), value)

    def get(self, key: str) -> ForensicResult | None:
        """Retrieve a result by key. Returns None if missing or expired."""
        self._evict_expired()
        entry = self._store.get(key)
        return entry[1] if entry is not None else None

    def _evict_expired(self) -> None:
        now = datetime.now(tz=timezone.utc)
        expired_keys = [
            k for k, (ts, _) in self._store.items() if now - ts > self._ttl
        ]
        for k in expired_keys:
            del self._store[k]


# ── Singleton ─────────────────────────────────────────────────────────────────
# Module-level instance. Safe on single-process uvicorn (--workers 1).
# Multiple workers would give each process its own store — intentionally avoided.

_store_instance: MemoryStore | None = None


def get_store(cfg: Settings | None = None) -> MemoryStore:
    """Return the module-level MemoryStore singleton, creating it on first call."""
    global _store_instance
    if _store_instance is None:
        from app.config import settings as default_settings

        s = cfg if cfg is not None else default_settings
        _store_instance = MemoryStore(
            ttl_seconds=s.result_store_ttl_seconds,
            max_items=s.result_store_max_items,
        )
    return _store_instance


def reset_store() -> None:
    """Reset the singleton. Used in tests to get a clean store between test runs."""
    global _store_instance
    _store_instance = None
