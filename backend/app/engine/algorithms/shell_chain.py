"""
Shell chain detection algorithm.

A shell account is one whose total transaction count (rows as sender + rows as
receiver) ≤ shell_max_total_transactions.  These are low-activity pass-through
accounts used to obscure the trail between a source and destination.

A valid shell chain is a path:
  non-shell → shell₁ → shell₂ → … → non-shell

where the number of edges ≥ shell_chain_min_hops (default 3).

Pattern labels:
  "shell_intermediary" — shell nodes in the chain
  "shell_source"       — non-shell source and destination nodes

Continuous score sub-factors (weights):
  f_depth      (40%) — more hops = deeper obfuscation attempt
  f_volume     (30%) — total $ pushed through the chain vs dataset median
  f_isolation  (20%) — how inactive are shell nodes; 1 txn = fully isolated
  f_velocity   (10%) — how fast funds moved through the chain

Clusters:
  All nodes in the discovered chain (both shell and non-shell endpoints).
"""

import logging
import math
from collections import deque

import networkx as nx
import pandas as pd

from app.models.algorithm_result import AlgorithmResult
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class ShellChainAlgorithm(BaseAlgorithm):

    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        max_txns = self.settings.shell_max_total_transactions
        min_hops = self.settings.shell_chain_min_hops
        median_amount = float(df["amount"].median())
        MAX_CHAINS = 10_000
        MAX_DEPTH = 10

        # Precompute per-edge timestamp range for velocity scoring
        edge_ts = (
            df.groupby(["sender_id", "receiver_id"])["timestamp"]
            .agg(ts_min="min", ts_max="max")
        )

        # ── Node classification ───────────────────────────────────────────
        is_shell: dict[str, bool] = {
            node: G.nodes[node].get("total_transactions", 0) <= max_txns
            for node in G.nodes()
        }

        non_shell_nodes = [n for n, shell in is_shell.items() if not shell]

        seen_paths: set[tuple[str, ...]] = set()

        # ── BFS from each non-shell source ───────────────────────────────
        for source in non_shell_nodes:

            if len(seen_paths) >= MAX_CHAINS:
                logger.warning("Shell chain cap %d reached. Stopping.", MAX_CHAINS)
                break

            self._bfs_from_source(
                G=G,
                source=source,
                is_shell=is_shell,
                min_hops=min_hops,
                max_depth=MAX_DEPTH,
                max_chains=MAX_CHAINS,
                seen_paths=seen_paths,
                result=result,
                edge_ts=edge_ts,
                median_amount=median_amount,
                max_txns=max_txns,
            )

        logger.info(
            "ShellChain: %d chains found, %d accounts flagged",
            len(seen_paths),
            len(result.account_flags),
        )

        return result

    # ── BFS traversal ─────────────────────────────────────────────────────

    def _bfs_from_source(
        self,
        G: nx.DiGraph,
        source: str,
        is_shell: dict[str, bool],
        min_hops: int,
        max_depth: int,
        max_chains: int,
        seen_paths: set[tuple[str, ...]],
        result: AlgorithmResult,
        edge_ts: pd.DataFrame,
        median_amount: float,
        max_txns: int,
    ) -> None:
        # queue entries: (current_node, path_tuple, visited_set)
        queue: deque = deque()
        queue.append((source, (source,), {source}))

        while queue:
            current, path, visited = queue.popleft()
            depth = len(path) - 1

            if depth >= max_depth:
                continue

            for neighbor in G.successors(current):

                if neighbor in visited:
                    continue

                new_path = path + (neighbor,)
                new_visited = visited | {neighbor}
                new_depth = depth + 1

                if is_shell.get(neighbor, False):
                    # Continue through shell intermediary
                    queue.append((neighbor, new_path, new_visited))

                else:
                    # Found non-shell destination
                    if new_depth >= min_hops:

                        intermediates = new_path[1:-1]
                        if all(is_shell.get(n, False) for n in intermediates):

                            if new_path not in seen_paths:
                                seen_paths.add(new_path)

                                # Flag endpoints
                                self._add_flag(result, new_path[0], "shell_source")
                                self._add_flag(result, new_path[-1], "shell_source")

                                # Flag intermediaries
                                for node in intermediates:
                                    self._add_flag(result, node, "shell_intermediary")

                                result.clusters.append(frozenset(new_path))

                                # Continuous score — all chain members share the same score
                                score = self._score_chain(
                                    new_path, G, edge_ts, median_amount,
                                    min_hops, max_txns,
                                )
                                for node in new_path:
                                    if result.account_scores.get(node, 0.0) < score:
                                        result.account_scores[node] = score

                    # Never continue past non-shell

    # ── Continuous scoring ─────────────────────────────────────────────────

    def _score_chain(
        self,
        path: tuple[str, ...],
        G: nx.DiGraph,
        edge_ts: pd.DataFrame,
        median_amount: float,
        min_hops: int,
        max_txns: int,
    ) -> float:
        hops = len(path) - 1

        # f_depth: more hops beyond minimum → more obfuscation
        f_depth = min(1.0, (hops - min_hops) / max(1, 10 - min_hops))

        # f_volume: total edge weight along the chain vs dataset median
        chain_volume = sum(
            G[path[i]][path[i + 1]].get("weight", 0.0)
            for i in range(hops)
            if G.has_edge(path[i], path[i + 1])
        )
        if median_amount > 0:
            f_volume = min(1.0, math.log10(max(1.0, chain_volume / median_amount)) / 4.0)
        else:
            f_volume = 0.0

        # f_isolation: how empty are the shell nodes? (1 txn = maximum isolation)
        shell_nodes = path[1:-1]
        if shell_nodes:
            avg_txns = sum(
                G.nodes[n].get("total_transactions", 1) for n in shell_nodes
            ) / len(shell_nodes)
            f_isolation = max(0.0, 1.0 - (avg_txns - 1) / max(1, max_txns - 1))
        else:
            f_isolation = 1.0

        # f_velocity: time span across all chain edges; < 1 week cap
        all_ts = []
        for i in range(hops):
            u, v = path[i], path[i + 1]
            try:
                row = edge_ts.loc[(u, v)]
                all_ts.extend([row["ts_min"], row["ts_max"]])
            except KeyError:
                pass
        if len(all_ts) >= 2:
            span_hours = (max(all_ts) - min(all_ts)).total_seconds() / 3600
            f_velocity = 1.0 - min(1.0, span_hours / 168.0)
        else:
            f_velocity = 0.5

        raw = (
            0.40 * f_depth
            + 0.30 * f_volume
            + 0.20 * f_isolation
            + 0.10 * f_velocity
        )
        return round(20.0 * raw, 2)
