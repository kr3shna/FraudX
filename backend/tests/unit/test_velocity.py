"""Unit tests for app/engine/algorithms/velocity.py."""

import pandas as pd
import pytest

from app.engine.algorithms.velocity import VelocityAlgorithm
from app.engine.graph_builder import build_graph


# ── Helpers ───────────────────────────────────────────────────────────────────

def _burst_df(n: int, gap_minutes: int = 10) -> pd.DataFrame:
    """n outgoing transactions from ACC_BURST, each gap_minutes apart."""
    base = pd.Timestamp("2024-01-01 10:00:00")
    timestamps = [base + pd.Timedelta(minutes=gap_minutes * i) for i in range(n)]
    return pd.DataFrame({
        "transaction_id": [f"VB{i:03d}" for i in range(n)],
        "sender_id": ["ACC_BURST"] * n,
        "receiver_id": [f"ACC_R{i:02d}" for i in range(n)],
        "amount": [500.0] * n,
        "timestamp": timestamps,
    })


# ── burst_activity ────────────────────────────────────────────────────────────

def test_burst_activity_detected(settings):
    """6 txns from same sender within 1 hour → burst_activity flagged."""
    df = _burst_df(6, gap_minutes=10)
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "burst_activity" in result.account_flags.get("ACC_BURST", [])
    assert result.account_scores.get("ACC_BURST", 0.0) > 0


def test_burst_activity_below_threshold_not_flagged(settings):
    """Only 4 txns in 1 hour (below burst_min_transactions=5) → not flagged."""
    df = _burst_df(4, gap_minutes=15)
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "burst_activity" not in result.account_flags.get("ACC_BURST", [])


def test_burst_spread_over_2_hours_not_flagged(settings):
    """5 txns spread across 2 hours — no 1-hour window contains all 5."""
    timestamps = pd.to_datetime([
        "2024-01-01 09:00:00",
        "2024-01-01 09:30:00",
        "2024-01-01 10:00:00",
        "2024-01-01 10:30:00",
        "2024-01-01 11:00:00",
    ])
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(5)],
        "sender_id": ["ACC_X"] * 5,
        "receiver_id": [f"ACC_R{i}" for i in range(5)],
        "amount": [500.0] * 5,
        "timestamp": timestamps,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "burst_activity" not in result.account_flags.get("ACC_X", [])


def test_burst_score_higher_for_more_txns(settings):
    """More txns in the same window → higher score."""
    df6 = _burst_df(6, gap_minutes=8)
    df10 = _burst_df(10, gap_minutes=5)
    G6, G10 = build_graph(df6), build_graph(df10)
    score6 = VelocityAlgorithm(settings).run(G6, df6).account_scores.get("ACC_BURST", 0.0)
    score10 = VelocityAlgorithm(settings).run(G10, df10).account_scores.get("ACC_BURST", 0.0)
    assert score10 > score6


# ── high_velocity ─────────────────────────────────────────────────────────────

def test_high_velocity_detected(settings):
    """15 txns from same sender within 24 hours → high_velocity flagged."""
    timestamps = pd.to_datetime([
        f"2024-01-01 {h:02d}:00:00" for h in range(15)
    ])
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(15)],
        "sender_id": ["ACC_FAST"] * 15,
        "receiver_id": [f"ACC_R{i}" for i in range(15)],
        "amount": [200.0] * 15,
        "timestamp": timestamps,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "high_velocity" in result.account_flags.get("ACC_FAST", [])


def test_high_velocity_not_flagged_when_spread_out(settings):
    """14 txns over 3 days — no single 24h window reaches 15."""
    timestamps = pd.to_datetime([
        f"2024-01-0{(i // 5) + 1} {(i % 5) * 4:02d}:00:00" for i in range(14)
    ])
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(14)],
        "sender_id": ["ACC_SLOW"] * 14,
        "receiver_id": [f"ACC_R{i}" for i in range(14)],
        "amount": [200.0] * 14,
        "timestamp": timestamps,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "high_velocity" not in result.account_flags.get("ACC_SLOW", [])


# ── velocity_spike ────────────────────────────────────────────────────────────

def test_velocity_spike_detected(settings):
    """1 txn in previous week, 10 txns in current week → ratio 10 ≥ 3.0."""
    prev_week = [pd.Timestamp("2024-01-01 00:00:00")]
    current_week = [
        pd.Timestamp("2024-01-08") + pd.Timedelta(hours=i) for i in range(10)
    ]
    all_ts = prev_week + current_week
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(len(all_ts))],
        "sender_id": ["ACC_SPIKE"] * len(all_ts),
        "receiver_id": [f"ACC_R{i}" for i in range(len(all_ts))],
        "amount": [100.0] * len(all_ts),
        "timestamp": all_ts,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "velocity_spike" in result.account_flags.get("ACC_SPIKE", [])


def test_velocity_spike_not_flagged_equal_weeks(settings):
    """Same number of txns each week → ratio 1.0 < 3.0 → not flagged."""
    week1 = [pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i * 2) for i in range(10)]
    week2 = [pd.Timestamp("2024-01-08") + pd.Timedelta(hours=i * 2) for i in range(10)]
    all_ts = week1 + week2
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(20)],
        "sender_id": ["ACC_NORMAL"] * 20,
        "receiver_id": [f"ACC_R{i}" for i in range(20)],
        "amount": [100.0] * 20,
        "timestamp": all_ts,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "velocity_spike" not in result.account_flags.get("ACC_NORMAL", [])


def test_velocity_spike_no_prior_history_not_flagged(settings):
    """All txns in current week only (no prior week data) → not flagged."""
    current_week = [pd.Timestamp("2024-01-08") + pd.Timedelta(hours=i) for i in range(10)]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(10)],
        "sender_id": ["ACC_NEW"] * 10,
        "receiver_id": [f"ACC_R{i}" for i in range(10)],
        "amount": [100.0] * 10,
        "timestamp": current_week,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "velocity_spike" not in result.account_flags.get("ACC_NEW", [])


# ── dormancy_break ────────────────────────────────────────────────────────────

def test_dormancy_break_detected(settings):
    """50-day gap then 6 txns in 48h → dormancy_break flagged."""
    early = [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")]
    burst = [pd.Timestamp("2024-03-01") + pd.Timedelta(hours=i * 6) for i in range(6)]
    all_ts = early + burst
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(len(all_ts))],
        "sender_id": ["ACC_DORMANT"] * len(all_ts),
        "receiver_id": [f"ACC_R{i}" for i in range(len(all_ts))],
        "amount": [1000.0] * len(all_ts),
        "timestamp": all_ts,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "dormancy_break" in result.account_flags.get("ACC_DORMANT", [])
    assert result.account_scores.get("ACC_DORMANT", 0.0) > 0


def test_dormancy_break_short_gap_not_flagged(settings):
    """15-day gap (< dormancy_min_days=30) → not flagged."""
    early = [pd.Timestamp("2024-01-01")]
    burst = [pd.Timestamp("2024-01-16") + pd.Timedelta(hours=i) for i in range(6)]
    all_ts = early + burst
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(len(all_ts))],
        "sender_id": ["ACC_X"] * len(all_ts),
        "receiver_id": [f"ACC_R{i}" for i in range(len(all_ts))],
        "amount": [1000.0] * len(all_ts),
        "timestamp": all_ts,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "dormancy_break" not in result.account_flags.get("ACC_X", [])


def test_dormancy_break_gap_but_low_activity_not_flagged(settings):
    """50-day gap then only 3 txns in 48h (below threshold=5) → not flagged."""
    early = [pd.Timestamp("2024-01-01")]
    burst = [pd.Timestamp("2024-03-01") + pd.Timedelta(hours=i * 10) for i in range(3)]
    all_ts = early + burst
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(len(all_ts))],
        "sender_id": ["ACC_Y"] * len(all_ts),
        "receiver_id": [f"ACC_R{i}" for i in range(len(all_ts))],
        "amount": [1000.0] * len(all_ts),
        "timestamp": all_ts,
    })
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert "dormancy_break" not in result.account_flags.get("ACC_Y", [])


# ── No clusters produced ──────────────────────────────────────────────────────

def test_velocity_produces_no_clusters(settings):
    """VelocityAlgorithm must never populate clusters — velocity accounts never form rings."""
    df = _burst_df(10, gap_minutes=5)
    G = build_graph(df)
    result = VelocityAlgorithm(settings).run(G, df)
    assert result.clusters == []
