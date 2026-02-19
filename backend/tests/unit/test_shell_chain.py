"""Unit tests for app/engine/algorithms/shell_chain.py."""

import pandas as pd
import pytest

from app.engine.algorithms.shell_chain import ShellChainAlgorithm
from app.engine.graph_builder import build_graph


def _run(df, settings):
    G = build_graph(df)
    return ShellChainAlgorithm(settings).run(G, df)


# ── Detection ─────────────────────────────────────────────────────────────────

def test_shell_chain_detected(shell_chain_df, settings):
    result = _run(shell_chain_df, settings)
    assert len(result.clusters) >= 1


def test_shell_intermediaries_flagged(shell_chain_df, settings):
    result = _run(shell_chain_df, settings)
    assert "shell_intermediary" in result.account_flags.get("ACC_SHELL1", [])
    assert "shell_intermediary" in result.account_flags.get("ACC_SHELL2", [])


def test_non_shell_endpoints_flagged_as_source(shell_chain_df, settings):
    result = _run(shell_chain_df, settings)
    assert "shell_source" in result.account_flags.get("ACC_RICH1", [])
    assert "shell_source" in result.account_flags.get("ACC_RICH2", [])


def test_shell_chain_cluster_contains_all_four(shell_chain_df, settings):
    result = _run(shell_chain_df, settings)
    chain_cluster = None
    for cluster in result.clusters:
        if {"ACC_RICH1", "ACC_SHELL1", "ACC_SHELL2", "ACC_RICH2"}.issubset(cluster):
            chain_cluster = cluster
            break
    assert chain_cluster is not None


# ── Non-detection ─────────────────────────────────────────────────────────────

def test_no_chain_all_high_degree(settings):
    """All nodes have many transactions — no shells, no chain detected."""
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(20)],
        "sender_id":      ["ACC_A"] * 10 + ["ACC_B"] * 10,
        "receiver_id":    ["ACC_B"] * 10 + ["ACC_C"] * 10,
        "amount":         [1000.0] * 20,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i % 12}:00:00" for i in range(20)]),
    })
    result = _run(df, settings)
    assert result.account_flags == {}


def test_short_chain_below_min_hops_not_detected(settings):
    """2-hop chain (below min_hops=3): RICH1 → SHELL1 → RICH2."""
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2",
                           "T3", "T4", "T5",  # extra txns so RICH1 is not a shell
                           "T6", "T7", "T8"],  # extra txns so RICH2 is not a shell
        "sender_id":      ["ACC_RICH1", "ACC_SHELL1",
                           "ACC_RICH1", "ACC_RICH1", "ACC_RICH1",
                           "ACC_X1", "ACC_X2", "ACC_X3"],
        "receiver_id":    ["ACC_SHELL1", "ACC_RICH2",
                           "ACC_Y1", "ACC_Y2", "ACC_Y3",
                           "ACC_RICH2", "ACC_RICH2", "ACC_RICH2"],
        "amount":         [5000.0] * 8,
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(8)]),
    })
    result = _run(df, settings)
    # ACC_SHELL1 has 2 txns (≤3 → shell), path RICH1→SHELL1→RICH2 = 2 hops < 3
    assert "ACC_SHELL1" not in result.account_flags


def test_fixture_file_shell_chain(settings):
    import pathlib
    from app.engine.parser import parse_csv
    content = (pathlib.Path("tests/fixtures/shell_chain.csv")).read_bytes()
    df, _ = parse_csv(content)
    result = _run(df, settings)
    assert "shell_intermediary" in result.account_flags.get("ACC_SHELL1", [])
    assert "shell_intermediary" in result.account_flags.get("ACC_SHELL2", [])
    assert "shell_source" in result.account_flags.get("ACC_RICH1", [])
    assert "shell_source" in result.account_flags.get("ACC_RICH2", [])
