"""Unit tests for app/engine/suppression.py (proportional suppression)."""

import pandas as pd
import pytest

from app.engine.graph_builder import build_graph
from app.engine.suppression import apply_suppression


# ── Rule 1: Payroll (smurfing_fan_out) ───────────────────────────────────────

def test_payroll_fan_out_suppressed_from_display(payroll_df, settings):
    """Strong payroll signal → smurfing_fan_out removed from display."""
    G = build_graph(payroll_df)
    flags = {"ACC_EMPLOYER": ["smurfing_fan_out"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, payroll_df, settings)
    assert "smurfing_fan_out" in suppressed_flags.get("ACC_EMPLOYER", [])


def test_payroll_multiplier_reduces_score(payroll_df, settings):
    """Strong payroll signal → multiplier well below 1.0."""
    G = build_graph(payroll_df)
    flags = {"ACC_EMPLOYER": ["smurfing_fan_out"]}
    _, multipliers = apply_suppression(flags, G, payroll_df, settings)
    assert multipliers.get("ACC_EMPLOYER", 1.0) <= 0.2


def test_irregular_amounts_not_suppressed_from_display(settings):
    """Fan-out with wildly varying amounts — not removed from display.
    Intervals are regular (1h) so a partial multiplier may apply, but the
    pattern must remain visible since amounts are clearly non-payroll."""
    receivers = [f"ACC_R{i:02d}" for i in range(1, 13)]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(12)],
        "sender_id":      ["ACC_SEND"] * 12,
        "receiver_id":    receivers,
        "amount":         [float(100 * (i + 1)) for i in range(12)],
        "timestamp":      pd.to_datetime([f"2024-01-01 {10 + i}:00:00" for i in range(12)]),
    })
    G = build_graph(df)
    flags = {"ACC_SEND": ["smurfing_fan_out"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, df, settings)
    # Amount CV is high → must not be hidden from display
    assert "smurfing_fan_out" not in suppressed_flags.get("ACC_SEND", [])


def test_irregular_intervals_not_suppressed(settings):
    """Same amounts but irregular timing — not fully suppressed."""
    receivers = [f"ACC_R{i:02d}" for i in range(1, 13)]
    timestamps = pd.to_datetime(
        ["2024-01-01 09:00:00"] * 6 + ["2024-01-10 09:00:00"] * 6
    )
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(12)],
        "sender_id":      ["ACC_SEND"] * 12,
        "receiver_id":    receivers,
        "amount":         [1200.0] * 12,
        "timestamp":      timestamps,
    })
    G = build_graph(df)
    flags = {"ACC_SEND": ["smurfing_fan_out"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, df, settings)
    assert "smurfing_fan_out" not in suppressed_flags.get("ACC_SEND", [])


def test_non_smurfing_flag_not_affected_by_payroll_rule(payroll_df, settings):
    """Payroll rule only touches smurfing_fan_out, not cycle flags."""
    G = build_graph(payroll_df)
    flags = {"ACC_EMPLOYER": ["smurfing_fan_out", "cycle_length_3"]}
    suppressed_flags, _ = apply_suppression(flags, G, payroll_df, settings)
    assert "cycle_length_3" not in suppressed_flags.get("ACC_EMPLOYER", [])


# ── Rule 2: Merchant (smurfing_fan_in) ───────────────────────────────────────

def test_merchant_fan_in_suppressed_from_display(merchant_df, settings):
    """Clear merchant pattern → smurfing_fan_in removed from display."""
    G = build_graph(merchant_df)
    flags = {"ACC_MERCHANT": ["smurfing_fan_in"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, merchant_df, settings)
    assert "smurfing_fan_in" in suppressed_flags.get("ACC_MERCHANT", [])


def test_merchant_multiplier_reduces_score(merchant_df, settings):
    """Clear merchant pattern → multiplier well below 1.0."""
    G = build_graph(merchant_df)
    flags = {"ACC_MERCHANT": ["smurfing_fan_in"]}
    _, multipliers = apply_suppression(flags, G, merchant_df, settings)
    assert multipliers.get("ACC_MERCHANT", 1.0) <= 0.2


def test_low_in_degree_not_suppressed(fan_in_df, settings):
    """12 senders — below merchant_min_in_degree(50) → not suppressed."""
    G = build_graph(fan_in_df)
    flags = {"ACC_RECV": ["smurfing_fan_in"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, fan_in_df, settings)
    assert "smurfing_fan_in" not in suppressed_flags.get("ACC_RECV", [])
    assert multipliers.get("ACC_RECV", 1.0) == 1.0


def test_high_in_degree_with_outgoing_not_fully_suppressed(settings):
    """High in-degree but account also sends money — not a clear merchant."""
    senders = [f"ACC_C{i:02d}" for i in range(1, 55)]
    base = pd.Timestamp("2024-01-01 10:00:00")
    df = pd.DataFrame({
        "transaction_id": [f"MC{i}" for i in range(54)] + ["OUT1"],
        "sender_id":      senders + ["ACC_MERCHANT"],
        "receiver_id":    ["ACC_MERCHANT"] * 54 + ["ACC_X"],
        "amount":         [100.0] * 55,
        "timestamp":      [base + pd.Timedelta(minutes=5 * i) for i in range(55)],
    })
    G = build_graph(df)
    flags = {"ACC_MERCHANT": ["smurfing_fan_in"]}
    suppressed_flags, _ = apply_suppression(flags, G, df, settings)
    # Has outgoing edge → not removed from display
    assert "smurfing_fan_in" not in suppressed_flags.get("ACC_MERCHANT", [])


def test_unrelated_account_not_suppressed(payroll_df, settings):
    """Suppression only touches accounts that have smurfing flags."""
    G = build_graph(payroll_df)
    flags = {"ACC_OTHER": ["cycle_length_3"]}
    suppressed_flags, multipliers = apply_suppression(flags, G, payroll_df, settings)
    assert suppressed_flags == {}
    assert multipliers == {}
