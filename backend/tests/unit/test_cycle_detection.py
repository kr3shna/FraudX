"""Unit tests for app/engine/algorithms/cycle_detection.py."""

import pandas as pd
import pytest

from app.engine.algorithms.cycle_detection import CycleDetectionAlgorithm
from app.engine.graph_builder import build_graph


def _run(df, settings):
    G = build_graph(df)
    return CycleDetectionAlgorithm(settings).run(G, df)


# ── Detection ─────────────────────────────────────────────────────────────────

def test_triangle_cycle_detected(triangle_df, settings):
    result = _run(triangle_df, settings)
    assert "ACC_A" in result.account_flags
    assert "ACC_B" in result.account_flags
    assert "ACC_C" in result.account_flags


def test_triangle_pattern_label(triangle_df, settings):
    result = _run(triangle_df, settings)
    assert "cycle_length_3" in result.account_flags["ACC_A"]


def test_triangle_produces_one_cluster(triangle_df, settings):
    result = _run(triangle_df, settings)
    assert len(result.clusters) == 1
    assert result.clusters[0] == {"ACC_A", "ACC_B", "ACC_C"}


def test_linear_chain_no_cycle(settings):
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "sender_id":      ["ACC_A", "ACC_B"],
        "receiver_id":    ["ACC_B", "ACC_C"],
        "amount":         [1000.0, 1000.0],
        "timestamp":      pd.to_datetime(["2024-01-01 10:00:00", "2024-01-01 11:00:00"]),
    })
    result = _run(df, settings)
    assert result.account_flags == {}
    assert result.clusters == []


def test_self_loop_not_detected(settings):
    """A single-node self-loop should not produce a cycle (min_length=3)."""
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "sender_id":      ["ACC_A", "ACC_B"],
        "receiver_id":    ["ACC_B", "ACC_A"],
        "amount":         [500.0, 500.0],
        "timestamp":      pd.to_datetime(["2024-01-01 10:00:00", "2024-01-01 11:00:00"]),
    })
    # 2-node cycle — below min_cycle_length=3
    result = _run(df, settings)
    assert result.account_flags == {}


def test_cycle_length_6_not_detected(settings):
    """Cycles longer than max_cycle_length (5) are ignored."""
    nodes = ["ACC_A", "ACC_B", "ACC_C", "ACC_D", "ACC_E", "ACC_F"]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(6)],
        "sender_id":      nodes,
        "receiver_id":    nodes[1:] + [nodes[0]],
        "amount":         [1000.0] * 6,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(6)]),
    })
    result = _run(df, settings)
    assert result.account_flags == {}


# ── Volume filter ─────────────────────────────────────────────────────────────

def test_tiny_volume_cycle_filtered_out(settings):
    """Cycle with negligible volume relative to the dataset median is discarded.

    The volume threshold is: threshold_pct × median_amount × cycle_length.
    Large non-cycle transactions (5000 each) push the median up to ~2500,
    making the threshold ≈ 75.  The cycle total volume (0.03) is far below it.
    """
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3", "B1", "B2", "B3"],
        "sender_id":      ["ACC_A", "ACC_B", "ACC_C", "ACC_X", "ACC_X", "ACC_X"],
        "receiver_id":    ["ACC_B", "ACC_C", "ACC_A", "ACC_Y", "ACC_Z", "ACC_W"],
        "amount":         [0.01, 0.01, 0.01, 5000.0, 5000.0, 5000.0],
        "timestamp":      pd.to_datetime([
            "2024-01-01 10:00:00", "2024-01-01 11:00:00", "2024-01-01 12:00:00",
            "2024-01-01 13:00:00", "2024-01-01 14:00:00", "2024-01-01 15:00:00",
        ]),
    })
    # median ≈ (0.01 + 5000)/2 = 2500; threshold = 0.01 × 2500 × 3 = 75
    # cycle volume = 0.03 << 75 → filtered out
    result = _run(df, settings)
    assert "ACC_A" not in result.account_flags
    assert "ACC_B" not in result.account_flags
    assert "ACC_C" not in result.account_flags


# ── Cycle lengths 4 and 5 ─────────────────────────────────────────────────────

def test_cycle_length_4_pattern_label(settings):
    nodes = ["ACC_A", "ACC_B", "ACC_C", "ACC_D"]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(4)],
        "sender_id":      nodes,
        "receiver_id":    nodes[1:] + [nodes[0]],
        "amount":         [5000.0] * 4,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(4)]),
    })
    result = _run(df, settings)
    for acc in nodes:
        assert "cycle_length_4" in result.account_flags.get(acc, [])


def test_cycle_length_5_pattern_label(settings):
    nodes = ["ACC_A", "ACC_B", "ACC_C", "ACC_D", "ACC_E"]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(5)],
        "sender_id":      nodes,
        "receiver_id":    nodes[1:] + [nodes[0]],
        "amount":         [5000.0] * 5,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(5)]),
    })
    result = _run(df, settings)
    for acc in nodes:
        assert "cycle_length_5" in result.account_flags.get(acc, [])
