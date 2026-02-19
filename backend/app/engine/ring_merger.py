"""
Ring merger — Union-Find over suspicious accounts.

Algorithm:
  1. Filter to accounts with score > suspicious_score_threshold.
  2. Initialize Union-Find with these accounts.
  3. For each cluster (cycle / smurfing / shell chain), union every pair of
     suspicious members.
  4. Groups with ≥ 2 members become named rings: RING_001, RING_002, …
     (sorted by group size DESC, ties broken alphabetically by min member).
  5. Singleton groups get ring_id = "NONE".

Returns a list of RingInfo named-tuples consumed by output_builder.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class RingInfo:
    ring_id: str
    member_accounts: list[str]        # sorted alphabetically
    pattern_type: str                  # "cycle" | "smurfing" | "shell" | "mixed"
    risk_score: float


# ── Union-Find ─────────────────────────────────────────────────────────────


class _UnionFind:
    def __init__(self, nodes: set[str]) -> None:
        self.parent: dict[str, str] = {n: n for n in nodes}
        self.rank: dict[str, int] = {n: 0 for n in nodes}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def get_groups(self) -> dict[str, set[str]]:
        groups: dict[str, set[str]] = {}
        for node in self.parent:
            root = self.find(node)
            groups.setdefault(root, set()).add(node)
        return groups


# ── Main entry point ───────────────────────────────────────────────────────


def merge_rings(
    all_clusters: list[set[str]],
    scores: dict[str, float],
    combined_flags: dict[str, list[str]],
    suppressed_flags: dict[str, list[str]],
    settings: Settings,
) -> list[RingInfo]:
    """
    Merge algorithm clusters into named fraud rings.

    Returns:
        Sorted list of RingInfo (multi-member rings only, ordered risk_score DESC).
        Singleton groups are represented by ring_id "NONE" on the account level
        but do NOT appear in this list.
    """
    threshold = settings.suspicious_score_threshold

    # Step 1: suspicious accounts only
    suspicious = {acc for acc, s in scores.items() if s >= threshold}
    if not suspicious:
        return []

    # Step 2: initialise UF
    uf = _UnionFind(suspicious)

    # Step 3: union cluster members that are both suspicious
    for cluster in all_clusters:
        members = [m for m in cluster if m in suspicious]
        for i in range(1, len(members)):
            uf.union(members[0], members[i])

    # Step 4: build ring objects from groups
    groups = uf.get_groups()
    rings: list[RingInfo] = []
    ring_counter = 1

    # Sort groups: size DESC, then min-member alphabetically for determinism
    sorted_groups = sorted(
        groups.values(),
        key=lambda g: (-len(g), min(g)),
    )

    for group in sorted_groups:
        if len(group) < 2:
            continue

        members_sorted = sorted(group)
        ring_id = f"RING_{ring_counter:03d}"
        ring_counter += 1

        # Determine effective patterns for the ring (after suppression)
        ring_patterns: set[str] = set()
        for acc in group:
            removed = set(suppressed_flags.get(acc, []))
            for p in combined_flags.get(acc, []):
                if p not in removed:
                    ring_patterns.add(p)

        pattern_type = _classify_pattern_type(ring_patterns)
        risk_score = _compute_ring_risk(group, scores, ring_patterns)

        rings.append(
            RingInfo(
                ring_id=ring_id,
                member_accounts=members_sorted,
                pattern_type=pattern_type,
                risk_score=risk_score,
            )
        )
        logger.debug(
            "Ring %s: %d members, type=%s, risk=%.1f",
            ring_id,
            len(group),
            pattern_type,
            risk_score,
        )

    logger.info("RingMerger: %d rings identified", len(rings))
    return rings


# ── Helpers ────────────────────────────────────────────────────────────────


_VELOCITY_PATTERNS = {"burst_activity", "high_velocity", "velocity_spike", "dormancy_break"}


def _classify_pattern_type(patterns: set[str]) -> str:
    has_cycle = any(p.startswith("cycle_") for p in patterns)
    has_smurfing = any(p.startswith("smurfing_") for p in patterns)
    has_shell = any(p.startswith("shell_") for p in patterns)
    has_velocity = bool(patterns & _VELOCITY_PATTERNS)

    active = sum([has_cycle, has_smurfing, has_shell, has_velocity])
    if active > 1:
        return "mixed"
    if has_cycle:
        return "cycle"
    if has_smurfing:
        return "smurfing"
    if has_shell:
        return "shell"
    if has_velocity:
        return "velocity"
    return "unknown"


def _compute_ring_risk(
    group: set[str],
    scores: dict[str, float],
    ring_patterns: set[str],
) -> float:
    member_scores = [scores.get(acc, 0.0) for acc in group]
    base_score = sum(member_scores) / len(member_scores)

    # Pattern diversity bonus
    distinct_types = 0
    if any(p.startswith("cycle_") for p in ring_patterns):
        distinct_types += 1
    if any(p.startswith("smurfing_") for p in ring_patterns):
        distinct_types += 1
    if any(p.startswith("shell_") for p in ring_patterns):
        distinct_types += 1

    pattern_bonus = min(15.0, (distinct_types - 1) * 5.0)

    # Cycle-3 bonus
    cycle3_bonus = 10.0 if "cycle_length_3" in ring_patterns else 0.0

    risk_score = min(100.0, round(base_score + pattern_bonus + cycle3_bonus, 1))
    return risk_score
