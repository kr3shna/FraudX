"""
False-positive suppression layer.

Instead of binary flag removal, suppression now applies a proportional multiplier
(0.0–1.0) to an account's smurfing score based on how strong the legitimate signal is.
A multiplier of 1.0 means no suppression; 0.1 means 90% reduction.

Suppression multiplier tiers:

  Rule 1 — Payroll pattern (smurfing_fan_out):
    Both CVs very low (< 50% of threshold)  → 0.1  (90% suppression, removed from display)
    Both CVs below threshold                → 0.2  (80% suppression, removed from display)
    One CV below threshold                  → 0.5  (50% suppression, still shown)
    Neither                                 → 1.0  (no suppression)

  Rule 2 — Merchant pattern (smurfing_fan_in):
    in_degree ≥ 2× min AND no outgoing      → 0.1  (90% suppression, removed from display)
    in_degree ≥ min AND no outgoing         → 0.2  (80% suppression, removed from display)
    in_degree ≥ 60% of min AND ≤ 3 outgoing → 0.5  (50% suppression, still shown)
    Otherwise                               → 1.0  (no suppression)

Returns:
  (suppressed_flags, suppression_multipliers)

  suppressed_flags:        account_id → list[pattern_label]  — flags hidden from display
                           (only for multiplier ≤ 0.2, i.e. strongly suppressed)
  suppression_multipliers: account_id → float (0–1)          — applied to smurfing score
"""

import logging

import networkx as nx
import pandas as pd

from app.config import Settings

logger = logging.getLogger(__name__)

# Multipliers at or below this are treated as "strong" suppression → hidden from display
_DISPLAY_SUPPRESS_THRESHOLD = 0.2


def apply_suppression(
    combined_flags: dict[str, list[str]],
    G: nx.DiGraph,
    df: pd.DataFrame,
    settings: Settings,
) -> tuple[dict[str, list[str]], dict[str, float]]:
    """
    Compute suppression decisions for all flagged accounts.

    Returns:
        suppressed_flags:        patterns to remove from display output
        suppression_multipliers: per-account score multiplier for smurfing category
    """
    suppressed_flags: dict[str, list[str]] = {}
    suppression_multipliers: dict[str, float] = {}

    for account, patterns in combined_flags.items():
        multiplier = 1.0
        removed: list[str] = []

        if "smurfing_fan_out" in patterns:
            mult = _payroll_multiplier(account, df, settings)
            if mult < multiplier:
                multiplier = mult
            if mult <= _DISPLAY_SUPPRESS_THRESHOLD:
                removed.append("smurfing_fan_out")
                logger.info(
                    "Suppressed smurfing_fan_out for %s (payroll mult=%.2f)", account, mult
                )

        if "smurfing_fan_in" in patterns:
            mult = _merchant_multiplier(account, G, settings)
            if mult < multiplier:
                multiplier = mult
            if mult <= _DISPLAY_SUPPRESS_THRESHOLD:
                removed.append("smurfing_fan_in")
                logger.info(
                    "Suppressed smurfing_fan_in for %s (merchant mult=%.2f)", account, mult
                )

        if multiplier < 1.0:
            suppression_multipliers[account] = multiplier
        if removed:
            suppressed_flags[account] = removed

    return suppressed_flags, suppression_multipliers


# ── Rule 1: Payroll ─────────────────────────────────────────────────────────


def _payroll_multiplier(account: str, df: pd.DataFrame, settings: Settings) -> float:
    outgoing = df[df["sender_id"] == account].sort_values("timestamp")
    if len(outgoing) < 2:
        return 1.0

    amounts = outgoing["amount"]
    mean_amt = amounts.mean()
    if mean_amt == 0:
        return 1.0
    amount_cv = amounts.std() / mean_amt

    intervals = outgoing["timestamp"].diff().dropna().dt.total_seconds()
    if len(intervals) == 0:
        return 1.0
    interval_mean = intervals.mean()
    interval_cv = intervals.std() / interval_mean if interval_mean > 0 else 0.0

    amt_thresh = settings.payroll_amount_cv_threshold
    int_thresh = settings.payroll_interval_cv_threshold

    # Both CVs very low → unmistakeable payroll
    if amount_cv < amt_thresh * 0.5 and interval_cv < int_thresh * 0.5:
        return 0.1

    # Both below threshold → strong payroll signal
    if amount_cv < amt_thresh and interval_cv < int_thresh:
        return 0.2

    # One below threshold → weak payroll signal
    if amount_cv < amt_thresh or interval_cv < int_thresh:
        return 0.5

    return 1.0


# ── Rule 2: Merchant ─────────────────────────────────────────────────────────


def _merchant_multiplier(account: str, G: nx.DiGraph, settings: Settings) -> float:
    in_deg = G.nodes[account].get("in_degree_count", 0)
    out_deg = G.nodes[account].get("out_degree_count", 0)
    min_in = settings.merchant_min_in_degree

    # Very high in-degree, zero outgoing → unmistakeable merchant
    if in_deg >= min_in * 2 and out_deg == 0:
        return 0.1

    # Meets threshold, zero outgoing → clear merchant
    if in_deg >= min_in and out_deg == 0:
        return 0.2

    # Moderate in-degree, few outgoing → possible merchant
    if in_deg >= int(min_in * 0.6) and out_deg <= 3:
        return 0.5

    # Some merchant characteristics
    if in_deg >= int(min_in * 0.3):
        return 0.8

    return 1.0
