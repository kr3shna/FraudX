"""Unit tests for app/engine/algorithms/smurfing.py."""

import pandas as pd
import pytest

from app.engine.algorithms.smurfing import SmurfingAlgorithm
from app.engine.graph_builder import build_graph


def _run(df, settings):
    G = build_graph(df)
    return SmurfingAlgorithm(settings).run(G, df)


# ── Fan-in ────────────────────────────────────────────────────────────────────

def test_fan_in_receiver_flagged(fan_in_df, settings):
    result = _run(fan_in_df, settings)
    assert "ACC_RECV" in result.account_flags
    assert "smurfing_fan_in" in result.account_flags["ACC_RECV"]


def test_fan_in_produces_cluster(fan_in_df, settings):
    result = _run(fan_in_df, settings)
    assert len(result.clusters) == 1
    cluster = result.clusters[0]
    assert "ACC_RECV" in cluster
    # All 12 senders are in the cluster
    for i in range(1, 13):
        assert f"ACC_S{i:02d}" in cluster


def test_fan_in_below_threshold_not_flagged(settings):
    """9 senders → 1 receiver — below smurfing_min_degree(10)."""
    senders = [f"ACC_S{i:02d}" for i in range(1, 10)]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(9)],
        "sender_id":      senders,
        "receiver_id":    ["ACC_RECV"] * 9,
        "amount":         [1000.0] * 9,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(9)]),
    })
    result = _run(df, settings)
    assert "ACC_RECV" not in result.account_flags


def test_fan_in_outside_window_not_flagged(settings):
    """10 senders → 1 receiver, but spread over 90h so no 72h window holds all 10."""
    senders = [f"ACC_S{i:02d}" for i in range(1, 11)]
    # 10h gaps → total span = 9 × 10h = 90h.
    # Any 72h window can contain at most floor(72/10)+1 = 8 transactions → < 10.
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(10)],
        "sender_id":      senders,
        "receiver_id":    ["ACC_RECV"] * 10,
        "amount":         [1000.0] * 10,
        "timestamp":      pd.date_range("2024-01-01 00:00:00", periods=10, freq="10h"),
    })
    result = _run(df, settings)
    assert "ACC_RECV" not in result.account_flags


# ── Fan-out ───────────────────────────────────────────────────────────────────

def test_fan_out_sender_flagged(fan_out_df, settings):
    result = _run(fan_out_df, settings)
    assert "ACC_SEND" in result.account_flags
    assert "smurfing_fan_out" in result.account_flags["ACC_SEND"]


def test_fan_out_produces_cluster(fan_out_df, settings):
    result = _run(fan_out_df, settings)
    assert len(result.clusters) >= 1
    cluster = result.clusters[0]
    assert "ACC_SEND" in cluster
    for i in range(1, 13):
        assert f"ACC_R{i:02d}" in cluster


def test_fan_out_below_threshold_not_flagged(settings):
    """1 sender → 9 receivers — below smurfing_min_degree(10)."""
    receivers = [f"ACC_R{i:02d}" for i in range(1, 10)]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(9)],
        "sender_id":      ["ACC_SEND"] * 9,
        "receiver_id":    receivers,
        "amount":         [1000.0] * 9,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(9)]),
    })
    result = _run(df, settings)
    assert "ACC_SEND" not in result.account_flags


# ── Fixture files ─────────────────────────────────────────────────────────────

def test_fan_in_fixture_file(settings):
    import pathlib
    from app.engine.parser import parse_csv
    content = (pathlib.Path("tests/fixtures/fan_in_smurfing.csv")).read_bytes()
    df, _ = parse_csv(content)
    result = _run(df, settings)
    assert "smurfing_fan_in" in result.account_flags.get("ACC_RECV", [])


def test_fan_out_fixture_file(settings):
    import pathlib
    from app.engine.parser import parse_csv
    content = (pathlib.Path("tests/fixtures/fan_out_smurfing.csv")).read_bytes()
    df, _ = parse_csv(content)
    result = _run(df, settings)
    assert "smurfing_fan_out" in result.account_flags.get("ACC_SEND", [])
