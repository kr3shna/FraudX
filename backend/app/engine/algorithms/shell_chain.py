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

        # Classify each node
        is_shell: dict[str, bool] = {
            acc: G.nodes[acc]["total_transactions"] <= max_txns
            for acc in G.nodes()
        }

        non_shell = [acc for acc, shell in is_shell.items() if not shell]

        found_chains: list[list[str]] = []

        for source in non_shell:
            chains = self._bfs_chains(G, source, is_shell, min_hops)
            found_chains.extend(chains)

        # Deduplicate by frozen path
        seen: set[tuple[str, ...]] = set()
        for chain in found_chains:
            key = tuple(chain)
            if key in seen:
                continue
            seen.add(key)

            # Flag nodes
            source_node = chain[0]
            dest_node = chain[-1]
            intermediaries = chain[1:-1]

            self._add_flag(result, source_node, "shell_source")
            self._add_flag(result, dest_node, "shell_source")
            for node in intermediaries:
                self._add_flag(result, node, "shell_intermediary")

            result.clusters.append(set(chain))
            logger.debug("Shell chain detected: %s", " → ".join(chain))

        logger.info(
            "ShellChain: %d chains found, %d accounts flagged",
            len(seen),
            len(result.account_flags),
        )
        return result

    def _bfs_chains(
        self,
        G: nx.DiGraph,
        source: str,
        is_shell: dict[str, bool],
        min_hops: int,
    ) -> list[list[str]]:
        """
        BFS from source through shell intermediaries.
        Returns all paths that end at a non-shell destination with ≥ min_hops edges.
        """
        chains: list[list[str]] = []
        # queue: (current_node, path_so_far)
        queue: deque[tuple[str, list[str]]] = deque()
        queue.append((source, [source]))

        while queue:
            current, path = queue.popleft()
            depth = len(path) - 1  # number of edges so far

            if depth > 10:  # safety cap to prevent runaway paths
                continue

            for neighbor in G.successors(current):
                if neighbor in path:  # no revisiting
                    continue

                new_path = path + [neighbor]
                new_depth = depth + 1

                if is_shell[neighbor]:
                    # Continue exploring through shell
                    queue.append((neighbor, new_path))
                else:
                    # Non-shell destination found
                    if new_depth >= min_hops:
                        # All intermediate nodes must be shells
                        intermediaries = new_path[1:-1]
                        if all(is_shell[n] for n in intermediaries):
                            chains.append(new_path)
                    # Do not continue past a non-shell destination

        return chains
