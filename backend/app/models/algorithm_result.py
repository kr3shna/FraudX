from dataclasses import dataclass, field


@dataclass
class AlgorithmResult:
    """
    Internal result produced by a single detection algorithm.
    Not exposed in the API — consumed by the suppression, scoring, and ring-merger layers.

    account_flags: maps account_id → list of pattern labels detected for that account
                   e.g. {"ACC_001": ["cycle_length_3", "smurfing_fan_in"]}

    clusters:      each entry is a set of account_ids that belong together
                   (same cycle, same smurfing cluster, same shell chain).
                   Used by the ring merger (Union-Find) to group accounts into rings.
    """

    account_flags: dict[str, list[str]] = field(default_factory=dict)
    clusters: list[set[str]] = field(default_factory=list)
