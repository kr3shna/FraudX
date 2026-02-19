"""
Cycle detection algorithm.

Strategy:
  1. Pre-filter using Strongly Connected Components (SCC) — only nodes inside
     an SCC of size ≥ min_cycle_length can participate in a cycle.
  2. For each SCC subgraph, enumerate simple cycles with networkx.simple_cycles.
  3. Filter by length (min_cycle_length ≤ len ≤ max_cycle_length).
  4. Filter by volume: cycle total edge weight ≥ threshold_pct × median_amount × length.
  5. For each surviving cycle, flag every member account and record the cluster.

Pattern labels:  "cycle_length_3" | "cycle_length_4" | "cycle_length_5"
"""

import logging

import networkx as nx
import pandas as pd

from app.models.algorithm_result import AlgorithmResult
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class CycleDetectionAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        min_len = self.settings.min_cycle_length
        max_len = self.settings.max_cycle_length
        threshold_pct = self.settings.cycle_volume_threshold_pct
        median_amount = float(df["amount"].median())

        # ── Step 1: SCC pre-filter ────────────────────────────────────────
        candidate_nodes: set[str] = set()
        for scc in nx.strongly_connected_components(G):
            if len(scc) >= min_len:
                candidate_nodes.update(scc)

        if not candidate_nodes:
            return result

        scc_subgraph = G.subgraph(candidate_nodes)

        # ── Step 2-4: Enumerate and filter cycles ─────────────────────────
        seen_cycles: set[frozenset[str]] = set()

        for cycle in nx.simple_cycles(scc_subgraph):
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
                logger.debug(
                    "Cycle %s discarded: volume %.2f < threshold %.2f",
                    cycle,
                    volume,
                    threshold,
                )
                continue

            # Deduplicate: same set of nodes = same cycle
            cycle_key = frozenset(cycle)
            if cycle_key in seen_cycles:
                continue
            seen_cycles.add(cycle_key)

            # ── Step 5: Flag and record ───────────────────────────────────
            pattern = f"cycle_length_{length}"
            for account in cycle:
                self._add_flag(result, account, pattern)

            result.clusters.append(set(cycle))
            logger.debug("Cycle detected: %s (length %d, volume %.2f)", cycle, length, volume)

        logger.info(
            "CycleDetection: %d unique cycles found, %d accounts flagged",
            len(seen_cycles),
            len(result.account_flags),
        )
        return result
