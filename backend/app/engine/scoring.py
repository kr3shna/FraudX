"""
Continuous scoring engine.

Combines per-category scores produced by each algorithm into a final suspicion score.

Category maxima:
  Cycle    max 40  — computed by CycleDetectionAlgorithm
  Smurfing max 25  — computed by SmurfingAlgorithm
  Shell    max 20  — computed by ShellChainAlgorithm
  Velocity max 15  — computed by VelocityAlgorithm
  Total    max 100

Rules:
  - Each algorithm stores its best (highest) continuous score per account in
    AlgorithmResult.account_scores.
  - Suppression multipliers (0–1) are applied to the smurfing score only.
  - Final score = cycle + (smurfing × multiplier) + shell + velocity.
  - Threshold to appear in output: suspicious_score_threshold (default 12.0).

Score reference (approximate, depends on data):
  Strong cycle alone      → 25–38
  Strong smurfing alone   → 15–23
  Strong shell alone      → 10–17
  Strong velocity alone   →  8–14
  Cycle + smurfing        → 40–60
  All four categories     → 65–95
"""


def compute_scores(
    cycle_scores: dict[str, float],
    smurfing_scores: dict[str, float],
    shell_scores: dict[str, float],
    suppression_multipliers: dict[str, float],
    velocity_scores: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Combine per-category algorithm scores into final suspicion scores.

    Args:
        cycle_scores:             account_id → cycle category score (0–40)
        smurfing_scores:          account_id → smurfing category score (0–25)
        shell_scores:             account_id → shell category score (0–20)
        suppression_multipliers:  account_id → multiplier applied to smurfing score (0–1)
        velocity_scores:          account_id → velocity category score (0–15); optional

    Returns:
        dict mapping account_id → suspicion_score (float, 0–100).
    """
    v_scores = velocity_scores if velocity_scores is not None else {}
    all_accounts = (
        set(cycle_scores) | set(smurfing_scores) | set(shell_scores) | set(v_scores)
    )
    scores: dict[str, float] = {}

    for acc in all_accounts:
        c  = cycle_scores.get(acc, 0.0)
        s  = smurfing_scores.get(acc, 0.0) * suppression_multipliers.get(acc, 1.0)
        sh = shell_scores.get(acc, 0.0)
        v  = v_scores.get(acc, 0.0)
        scores[acc] = round(c + s + sh + v, 1)

    return scores
