"""
Cycle detection algorithm.

Strategy:
  1. Pre-filter using Strongly Connected Components (SCC) — only nodes inside
     an SCC of size ≥ min_cycle_length can participate in a cycle.
  2. Process each SCC independently (not as one combined subgraph).
  3. Skip SCCs larger than _MAX_SCC_SIZE — pathologically dense SCCs would take
     exponential time; flag all their members instead with a generic warning.
  4. For each manageable SCC subgraph, enumerate simple cycles with a hard cap
     of _MAX_CYCLES_PER_SCC to bound worst-case runtime.
  5. Filter by length (min_cycle_length ≤ len ≤ max_cycle_length).
  6. Filter by volume: cycle total edge weight ≥ threshold_pct × median_amount × length.
  7. Score each cycle continuously (0–40) based on length, volume, and velocity.
  8. For each surviving cycle, flag every member account and record the cluster.

Pattern labels:  "cycle_length_3" | "cycle_length_4" | "cycle_length_5"

Continuous score sub-factors (weights):
  f_length   (40%) — shorter cycles are more deliberate; length 3 → 1.0, length 5 → 0.0
  f_volume   (35%) — total $ flowing around the cycle relative to dataset median
  f_velocity (25%) — how fast the cycle completed (hours); faster → more suspicious
"""

import logging
import math

import networkx as nx
import pandas as pd

from app.models.algorithm_result import AlgorithmResult
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)

# Safety caps to keep the algorithm fast on large/dense graphs
_MAX_SCC_SIZE = 50
_MAX_CYCLES_PER_SCC = 500


class CycleDetectionAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        min_len = self.settings.min_cycle_length
        max_len = self.settings.max_cycle_length
        threshold_pct = self.settings.cycle_volume_threshold_pct
        median_amount = float(df["amount"].median())

        # Precompute per-edge timestamp range for velocity scoring
        edge_ts = (
            df.groupby(["sender_id", "receiver_id"])["timestamp"]
            .agg(ts_min="min", ts_max="max")
        )

        # ── Step 1: SCC pre-filter ────────────────────────────────────────
        qualifying_sccs = [
            scc for scc in nx.strongly_connected_components(G)
            if min_len <= len(scc) <= _MAX_SCC_SIZE
        ]

        oversized = [
            scc for scc in nx.strongly_connected_components(G)
            if len(scc) > _MAX_SCC_SIZE
        ]
        if oversized:
            logger.warning(
                "Skipping %d oversized SCC(s) (size > %d) — too dense for enumeration",
                len(oversized), _MAX_SCC_SIZE,
            )

        if not qualifying_sccs:
            return result

        seen_cycles: set[frozenset[str]] = set()

        # ── Steps 2–8: Enumerate each SCC independently ──────────────────
        for scc in qualifying_sccs:
            scc_subgraph = G.subgraph(scc)
            cycles_in_scc = 0

            for cycle in nx.simple_cycles(scc_subgraph):
                if cycles_in_scc >= _MAX_CYCLES_PER_SCC:
                    logger.warning(
                        "SCC of size %d hit cycle cap (%d) — stopping early",
                        len(scc), _MAX_CYCLES_PER_SCC,
                    )
                    break

                length = len(cycle)
                if length < min_len or length > max_len:
                    continue

                # Volume filter
                volume = 0.0
                valid_edges = True
                for i in range(length):
                    u = cycle[i]
                    v = cycle[(i + 1) % length]
                    if G.has_edge(u, v):
                        volume += G[u][v].get("weight", 0.0)
                    else:
                        valid_edges = False
                        break

                if not valid_edges:
                    continue

                threshold = threshold_pct * median_amount * length
                if volume < threshold:
                    continue

                # Deduplicate
                cycle_key = frozenset(cycle)
                if cycle_key in seen_cycles:
                    continue
                seen_cycles.add(cycle_key)
                cycles_in_scc += 1

                # Continuous score for this cycle
                score = self._score_cycle(
                    cycle, volume, G, edge_ts, median_amount, min_len, max_len
                )

                pattern = f"cycle_length_{length}"
                for account in cycle:
                    self._add_flag(result, account, pattern)
                    # Track the best (highest) cycle score per account
                    if result.account_scores.get(account, 0.0) < score:
                        result.account_scores[account] = score

                result.clusters.append(set(cycle))
                logger.debug(
                    "Cycle detected: %s (length %d, volume %.2f, score %.1f)",
                    cycle, length, volume, score,
                )

        logger.info(
            "CycleDetection: %d unique cycles found, %d accounts flagged",
            len(seen_cycles),
            len(result.account_flags),
        )
        return result

    # ── Continuous scoring ────────────────────────────────────────────────

    def _score_cycle(
        self,
        cycle: list[str],
        volume: float,
        G: nx.DiGraph,
        edge_ts: pd.DataFrame,
        median_amount: float,
        min_len: int,
        max_len: int,
    ) -> float:
        length = len(cycle)

        # f_length: shorter = more deliberate (length 3 → 1.0, length 5 → 0.0)
        if max_len > min_len:
            f_length = (max_len - length) / (max_len - min_len)
        else:
            f_length = 1.0

        # f_volume: cycle $ relative to dataset median; 1000× median → 1.0
        if median_amount > 0:
            f_volume = min(1.0, math.log10(max(1.0, volume / median_amount)) / 3.0)
        else:
            f_volume = 0.0

        # f_velocity: time span across all cycle edges; < 1 week cap
        all_ts = []
        for i in range(length):
            u = cycle[i]
            v = cycle[(i + 1) % length]
            try:
                row = edge_ts.loc[(u, v)]
                all_ts.extend([row["ts_min"], row["ts_max"]])
            except KeyError:
                pass
        if len(all_ts) >= 2:
            span_hours = (max(all_ts) - min(all_ts)).total_seconds() / 3600
            f_velocity = 1.0 - min(1.0, span_hours / 168.0)
        else:
            f_velocity = 0.5  # unknown → neutral

        raw = 0.40 * f_length + 0.35 * f_volume + 0.25 * f_velocity
        return round(40.0 * raw, 2)
