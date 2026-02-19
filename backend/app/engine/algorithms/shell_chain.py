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

Clusters:
  All nodes in the discovered chain (both shell and non-shell endpoints).
"""

import logging
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
        MAX_CHAINS = 10_000
        MAX_DEPTH = 10

        # ── Node classification (safe) ───────────────────────────
        is_shell: dict[str, bool] = {
            node: G.nodes[node].get("total_transactions", 0) <= max_txns
            for node in G.nodes()
        }

        non_shell_nodes = [n for n, shell in is_shell.items() if not shell]

        seen_paths: set[tuple[str, ...]] = set()

        # ── BFS from each non-shell source ───────────────────────
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
            )

        logger.info(
            "ShellChain: %d chains found, %d accounts flagged",
            len(seen_paths),
            len(result.account_flags),
        )

        return result

    # ─────────────────────────────────────────────────────────────
    # BFS traversal from a single source
    # ─────────────────────────────────────────────────────────────
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
    ):
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

                        # Ensure all intermediates are shells
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

                    # Never continue past non-shell
