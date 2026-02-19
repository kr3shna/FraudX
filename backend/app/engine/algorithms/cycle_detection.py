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
  7. For each surviving cycle, flag every member account and record the cluster.

Pattern labels:  "cycle_length_3" | "cycle_length_4" | "cycle_length_5"
"""

import logging

import networkx as nx
import pandas as pd

from app.models.algorithm_result import AlgorithmResult
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)

# Safety caps to keep the algorithm fast on large/dense graphs
_MAX_SCC_SIZE = 50       # SCCs larger than this are skipped (too dense to enumerate)
_MAX_CYCLES_PER_SCC = 500  # Stop enumerating after this many cycles per SCC


class CycleDetectionAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        min_len = self.settings.min_cycle_length
        max_len = self.settings.max_cycle_length
        threshold_pct = self.settings.cycle_volume_threshold_pct
        median_amount = float(df["amount"].median())

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

        # ── Step 2-6: Enumerate each SCC independently ───────────────────
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

                # Compute cycle volume (sum of edge weights along the cycle)
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

                # ── Step 7: Flag and record ───────────────────────────────
                pattern = f"cycle_length_{length}"
                for account in cycle:
                    self._add_flag(result, account, pattern)

                result.clusters.append(set(cycle))
                logger.debug(
                    "Cycle detected: %s (length %d, volume %.2f)", cycle, length, volume
                )

        logger.info(
            "CycleDetection: %d unique cycles found, %d accounts flagged",
            len(seen_cycles),
            len(result.account_flags),
        )
        return result
