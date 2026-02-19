"""
False-positive suppression layer.

Two rules are applied to the combined flag map produced by all algorithms:

  Rule 1 — Payroll pattern (suppress smurfing_fan_out):
    If a fan-out account's outgoing transactions have:
      - Amount CV (std/mean) < payroll_amount_cv_threshold (0.15), AND
      - Interval CV (std/mean of consecutive timestamps) < payroll_interval_cv_threshold (0.2)
    → Remove the "smurfing_fan_out" flag (regular automated disbursement).

  Rule 2 — Merchant pattern (suppress smurfing_fan_in):
    If a fan-in account has:
      - In-degree ≥ merchant_min_in_degree (50), AND
      - No outgoing edges in the graph
    → Remove the "smurfing_fan_in" flag (legitimate merchant/retailer).

Returns:
  suppressed_flags: dict[account_id → list[pattern_label]] — flags removed per account.
  The CALLER is responsible for subtracting suppressed_flags from combined_flags.
"""

import logging

import networkx as nx
import pandas as pd

from app.config import Settings

logger = logging.getLogger(__name__)


def apply_suppression(
    combined_flags: dict[str, list[str]],
    G: nx.DiGraph,
    df: pd.DataFrame,
    settings: Settings,
) -> dict[str, list[str]]:
    """
    Identify flags that should be suppressed.

    Returns:
        A dict mapping account_id → list of pattern labels to REMOVE.
        Patterns not in this dict (or accounts not in this dict) are untouched.
    """
    suppressed: dict[str, list[str]] = {}

    for account, patterns in combined_flags.items():
        removed: list[str] = []

        if "smurfing_fan_out" in patterns and _is_payroll(account, df, settings):
            removed.append("smurfing_fan_out")
            logger.info("Suppressed smurfing_fan_out for %s (payroll pattern)", account)

        if "smurfing_fan_in" in patterns and _is_merchant(account, G, settings):
            removed.append("smurfing_fan_in")
            logger.info("Suppressed smurfing_fan_in for %s (merchant pattern)", account)

        if removed:
            suppressed[account] = removed

    return suppressed


# ── Rule 1: Payroll ────────────────────────────────────────────────────────


def _is_payroll(account: str, df: pd.DataFrame, settings: Settings) -> bool:
    outgoing = df[df["sender_id"] == account].sort_values("timestamp")
    if len(outgoing) < 2:
        return False

    # Amount CV
    amounts = outgoing["amount"]
    mean_amt = amounts.mean()
    if mean_amt == 0:
        return False
    amount_cv = amounts.std() / mean_amt
    if amount_cv >= settings.payroll_amount_cv_threshold:
        return False

    # Interval CV
    intervals = outgoing["timestamp"].diff().dropna().dt.total_seconds()
    if len(intervals) < 1:
        return True  # only 1 interval — cannot compute CV, treat as consistent
    interval_mean = intervals.mean()
    if interval_mean == 0:
        return True  # all at same timestamp — effectively zero variation
    interval_cv = intervals.std() / interval_mean
    if interval_cv >= settings.payroll_interval_cv_threshold:
        return False

    return True


# ── Rule 2: Merchant ───────────────────────────────────────────────────────


def _is_merchant(account: str, G: nx.DiGraph, settings: Settings) -> bool:
    in_deg = G.nodes[account].get("in_degree_count", 0)
    if in_deg < settings.merchant_min_in_degree:
        return False
    # No outgoing edges (account only receives, never sends)
    return G.out_degree(account) == 0
