from dataclasses import dataclass, field


@dataclass
class AlgorithmResult:
    """
    Internal result produced by a single detection algorithm.
    Not exposed in the API — consumed by the suppression, scoring, and ring-merger layers.

    account_flags:  account_id → list of pattern labels (used for display + ring classification)
    account_scores: account_id → continuous score within this algorithm's category (0–category_max)
                    e.g. CycleDetection stores values 0–40, Smurfing 0–25, ShellChain 0–20.
                    The scoring engine combines these three dicts into a final suspicion score.
    clusters:       each entry is a set of account_ids that belong together (same cycle,
                    smurfing cluster, or shell chain). Used by the ring merger.
    """

    account_flags: dict[str, list[str]] = field(default_factory=dict)
    account_scores: dict[str, float] = field(default_factory=dict)
    clusters: list[set[str]] = field(default_factory=list)
