"""Abstract base class for all detection algorithms."""

from abc import ABC, abstractmethod

import networkx as nx
import pandas as pd

from app.config import Settings
from app.models.algorithm_result import AlgorithmResult


class BaseAlgorithm(ABC):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        """
        Execute the detection algorithm.

        Args:
            G:  NetworkX DiGraph with node attributes from graph_builder.
            df: Clean transaction DataFrame (post-validation, typed).

        Returns:
            AlgorithmResult with flagged accounts and discovered clusters.
        """
        ...

    def _add_flag(
        self, result: AlgorithmResult, account_id: str, pattern: str
    ) -> None:
        """Add a pattern label to an account, deduplicating automatically."""
        flags = result.account_flags.setdefault(account_id, [])
        if pattern not in flags:
            flags.append(pattern)
