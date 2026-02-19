from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.models.response import (
    ForensicResult,
    ForensicSummary,
    FraudRing,
    SuspiciousAccount,
)
from app.store.memory_store import MemoryStore, get_store, reset_store


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_result(account_id: str = "ACC_001") -> ForensicResult:
    """Minimal valid ForensicResult for store tests."""
    return ForensicResult(
        suspicious_accounts=[
            SuspiciousAccount(
                account_id=account_id,
                suspicion_score=65.0,
                detected_patterns=["cycle_length_3"],
                ring_id="RING_001",
            )
        ],
        fraud_rings=[
            FraudRing(
                ring_id="RING_001",
                member_accounts=[account_id],
                pattern_type="cycle",
                risk_score=70.0,
            )
        ],
        summary=ForensicSummary(
            total_accounts_analyzed=10,
            suspicious_accounts_flagged=1,
            fraud_rings_detected=1,
            processing_time_seconds=0.5,
        ),
    )


def _make_store(ttl_seconds: int = 3600, max_items: int = 10) -> MemoryStore:
    return MemoryStore(ttl_seconds=ttl_seconds, max_items=max_items)


# ── Basic set / get ───────────────────────────────────────────────────────────

def test_set_and_get_returns_stored_result():
    store = _make_store()
    result = _make_result()
    store.set("token_1", result)
    retrieved = store.get("token_1")
    assert retrieved is not None
    assert retrieved.suspicious_accounts[0].account_id == "ACC_001"


def test_get_missing_key_returns_none():
    store = _make_store()
    assert store.get("nonexistent") is None


def test_set_overwrites_existing_key():
    store = _make_store()
    store.set("token_1", _make_result("ACC_001"))
    store.set("token_1", _make_result("ACC_999"))
    result = store.get("token_1")
    assert result is not None
    assert result.suspicious_accounts[0].account_id == "ACC_999"


# ── TTL expiry ────────────────────────────────────────────────────────────────

def test_expired_entry_returns_none(monkeypatch):
    store = _make_store(ttl_seconds=60)
    store.set("token_exp", _make_result())

    # Backdate the stored timestamp so it appears expired.
    key = "token_exp"
    ts, value = store._store[key]
    store._store[key] = (ts - timedelta(seconds=120), value)

    assert store.get("token_exp") is None


def test_non_expired_entry_is_returned(monkeypatch):
    store = _make_store(ttl_seconds=3600)
    store.set("token_ok", _make_result())
    assert store.get("token_ok") is not None


def test_expired_entries_evicted_on_set(monkeypatch):
    store = _make_store(ttl_seconds=60, max_items=10)
    store.set("token_a", _make_result("ACC_A"))
    store.set("token_b", _make_result("ACC_B"))

    # Backdate both entries to expired.
    for key in ("token_a", "token_b"):
        ts, val = store._store[key]
        store._store[key] = (ts - timedelta(seconds=120), val)

    # Trigger eviction via a new set.
    store.set("token_c", _make_result("ACC_C"))

    assert store.get("token_a") is None
    assert store.get("token_b") is None
    assert store.get("token_c") is not None


# ── Capacity / LRU eviction ───────────────────────────────────────────────────

def test_oldest_entry_evicted_when_at_capacity():
    store = _make_store(max_items=3)
    store.set("t1", _make_result("A1"))
    store.set("t2", _make_result("A2"))
    store.set("t3", _make_result("A3"))
    # Adding a 4th item should evict t1 (oldest).
    store.set("t4", _make_result("A4"))

    assert store.get("t1") is None   # evicted
    assert store.get("t2") is not None
    assert store.get("t3") is not None
    assert store.get("t4") is not None


def test_refreshing_existing_key_does_not_evict_other_entries():
    store = _make_store(max_items=3)
    store.set("t1", _make_result("A1"))
    store.set("t2", _make_result("A2"))
    store.set("t3", _make_result("A3"))
    # Re-set an existing key — should not count as a new item.
    store.set("t1", _make_result("A1_updated"))

    assert store.get("t1").suspicious_accounts[0].account_id == "A1_updated"
    assert store.get("t2") is not None
    assert store.get("t3") is not None


def test_capacity_one_always_holds_only_latest():
    store = _make_store(max_items=1)
    store.set("t1", _make_result("A1"))
    store.set("t2", _make_result("A2"))
    assert store.get("t1") is None
    assert store.get("t2") is not None


# ── Singleton (get_store / reset_store) ───────────────────────────────────────

def test_get_store_returns_same_instance():
    reset_store()
    cfg = Settings(result_store_ttl_seconds=600, result_store_max_items=5)
    s1 = get_store(cfg)
    s2 = get_store(cfg)
    assert s1 is s2


def test_reset_store_creates_fresh_instance():
    reset_store()
    cfg = Settings(result_store_ttl_seconds=600, result_store_max_items=5)
    s1 = get_store(cfg)
    s1.set("x", _make_result())
    reset_store()
    s2 = get_store(cfg)
    assert s2.get("x") is None
    assert s1 is not s2
