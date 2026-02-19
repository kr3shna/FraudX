"""
Categorical scoring engine.

Category table (sum of maxima = 100):

  Cycle    (max 40): cycle_length_3=40, cycle_length_4=32, cycle_length_5=25
  Smurfing (max 25): smurfing_fan_in=25, smurfing_fan_out=22
  Shell    (max 20): shell_intermediary=20, shell_source=15
  Velocity (max 15): burst_activity=15, dormancy_break=13,
                     high_velocity=11, velocity_spike=9

Rules:
  - Within each category:  take the HIGHEST single pattern score.
  - Across categories:     sum the four category scores.
  - Velocity-only accounts (cycle + smurfing + shell = 0): hard cap at 35.
  - Only accounts with total score > suspicious_score_threshold (40.0) are
    returned in the final output, but this function scores ALL accounts.
"""

import networkx as nx

from app.config import Settings

# ── Pattern → point value ─────────────────────────────────────────────────
_PATTERN_SCORES: dict[str, int] = {
    # Cycle
    "cycle_length_3": 40,
    "cycle_length_4": 32,
    "cycle_length_5": 25,
    # Smurfing
    "smurfing_fan_in": 25,
    "smurfing_fan_out": 22,
    # Shell
    "shell_intermediary": 20,
    "shell_source": 15,
    # Velocity
    "burst_activity": 15,
    "dormancy_break": 13,
    "high_velocity": 11,
    "velocity_spike": 9,
}

# ── Pattern → category ────────────────────────────────────────────────────
_CYCLE_PATTERNS = {"cycle_length_3", "cycle_length_4", "cycle_length_5"}
_SMURFING_PATTERNS = {"smurfing_fan_in", "smurfing_fan_out"}
_SHELL_PATTERNS = {"shell_intermediary", "shell_source"}
_VELOCITY_PATTERNS = {"burst_activity", "dormancy_break", "high_velocity", "velocity_spike"}

_VELOCITY_ONLY_CAP = 35.0


def compute_scores(
    combined_flags: dict[str, list[str]],
    suppressed_flags: dict[str, list[str]],
    G: nx.DiGraph,
    settings: Settings,
) -> dict[str, float]:
    """
    Compute a suspicion score for every flagged account.

    Args:
        combined_flags:  raw flags from all algorithms (before suppression).
        suppressed_flags: flags to remove (from suppression layer).
        G:               the transaction graph (not used for scoring, kept for API consistency).
        settings:        configuration (threshold used by callers, not here).

    Returns:
        dict mapping account_id → suspicion_score (float, 0–100).
        Accounts with zero effective flags score 0 and are excluded from output
        by the output builder.
    """
    scores: dict[str, float] = {}

    for account, raw_patterns in combined_flags.items():
        removed = set(suppressed_flags.get(account, []))
        effective = [p for p in raw_patterns if p not in removed]

        score = _score_patterns(effective)
        scores[account] = score

    return scores


def _score_patterns(patterns: list[str]) -> float:
    if not patterns:
        return 0.0

    pattern_set = set(patterns)

    cycle_score = max(
        (_PATTERN_SCORES[p] for p in pattern_set & _CYCLE_PATTERNS), default=0
    )
    smurfing_score = max(
        (_PATTERN_SCORES[p] for p in pattern_set & _SMURFING_PATTERNS), default=0
    )
    shell_score = max(
        (_PATTERN_SCORES[p] for p in pattern_set & _SHELL_PATTERNS), default=0
    )
    velocity_score = max(
        (_PATTERN_SCORES[p] for p in pattern_set & _VELOCITY_PATTERNS), default=0
    )

    total = float(cycle_score + smurfing_score + shell_score + velocity_score)

    # Velocity-only hard cap
    if cycle_score == 0 and smurfing_score == 0 and shell_score == 0:
        total = min(total, _VELOCITY_ONLY_CAP)

    return total
