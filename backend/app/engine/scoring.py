"""
Continuous scoring engine.

Combines per-category scores produced by each algorithm into a final suspicion score.

Category maxima (unchanged from v1):
  Cycle    max 40  — computed by CycleDetectionAlgorithm
  Smurfing max 25  — computed by SmurfingAlgorithm
  Shell    max 20  — computed by ShellChainAlgorithm
  Total    max 85

Rules:
  - Each algorithm stores its best (highest) continuous score per account in
    AlgorithmResult.account_scores.
  - Suppression multipliers (0–1) are applied to the smurfing score only.
  - Final score = cycle_score + (smurfing_score × multiplier) + shell_score.
  - Threshold to appear in output: suspicious_score_threshold (default 15.0).

Score reference (approximate, depends on data):
  Strong cycle alone    → 25–38
  Strong smurfing alone → 15–23
  Strong shell alone    → 10–17
  Cycle + smurfing      → 40–60
  All three categories  → 55–80
"""


def compute_scores(
    cycle_scores: dict[str, float],
    smurfing_scores: dict[str, float],
    shell_scores: dict[str, float],
    suppression_multipliers: dict[str, float],
) -> dict[str, float]:
    """
    Combine per-category algorithm scores into final suspicion scores.

    Args:
        cycle_scores:             account_id → cycle category score (0–40)
        smurfing_scores:          account_id → smurfing category score (0–25)
        shell_scores:             account_id → shell category score (0–20)
        suppression_multipliers:  account_id → multiplier applied to smurfing score (0–1)

    Returns:
        dict mapping account_id → suspicion_score (float, 0–85).
    """
    all_accounts = set(cycle_scores) | set(smurfing_scores) | set(shell_scores)
    scores: dict[str, float] = {}

    for acc in all_accounts:
        c  = cycle_scores.get(acc, 0.0)
        s  = smurfing_scores.get(acc, 0.0) * suppression_multipliers.get(acc, 1.0)
        sh = shell_scores.get(acc, 0.0)
        scores[acc] = round(c + s + sh, 1)

    return scores
