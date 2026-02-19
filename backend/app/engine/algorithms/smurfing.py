"""
Smurfing detection algorithm.

Fan-in:  many unique senders → one receiver within a sliding 72-hour window.
Fan-out: one sender → many unique receivers within a sliding 72-hour window.

Strategy per direction:
  - For each candidate account, sort their transactions by timestamp.
  - Slide a window anchored at each transaction's timestamp.
  - If unique counterparts in the window ≥ smurfing_min_degree → flag.

Pattern labels:
  "smurfing_fan_in"  — applied to the receiver account
  "smurfing_fan_out" — applied to the sender account

Clusters:
  fan-in:  {receiver} ∪ {all senders in the triggering window}
  fan-out: {sender}   ∪ {all receivers in the triggering window}
"""

import logging

import pandas as pd

from app.models.algorithm_result import AlgorithmResult
import networkx as nx
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class SmurfingAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()
        window = pd.Timedelta(hours=self.settings.smurfing_window_hours)
        min_degree = self.settings.smurfing_min_degree

        self._detect_fan_in(df, result, window, min_degree)
        self._detect_fan_out(df, result, window, min_degree)

        logger.info(
            "SmurfingDetection: %d accounts flagged, %d clusters",
            len(result.account_flags),
            len(result.clusters),
        )
        return result

    # ── Fan-in ────────────────────────────────────────────────────────────

    def _detect_fan_in(
        self,
        df: pd.DataFrame,
        result: AlgorithmResult,
        window: pd.Timedelta,
        min_degree: int,
    ) -> None:
        for receiver in df["receiver_id"].unique():
            incoming = (
                df[df["receiver_id"] == receiver]
                .sort_values("timestamp")
                .reset_index(drop=True)
            )
            if len(incoming) < min_degree:
                continue

            timestamps = incoming["timestamp"].values
            senders = incoming["sender_id"].values

            for i in range(len(timestamps)):
                window_end = timestamps[i] + window
                mask = (timestamps >= timestamps[i]) & (timestamps <= window_end)
                unique_senders = set(senders[mask])
                if len(unique_senders) >= min_degree:
                    self._add_flag(result, receiver, "smurfing_fan_in")
                    result.clusters.append({receiver} | unique_senders)
                    logger.debug(
                        "Fan-in: %s ← %d senders", receiver, len(unique_senders)
                    )
                    break  # one triggering window is enough

    # ── Fan-out ───────────────────────────────────────────────────────────

    def _detect_fan_out(
        self,
        df: pd.DataFrame,
        result: AlgorithmResult,
        window: pd.Timedelta,
        min_degree: int,
    ) -> None:
        for sender in df["sender_id"].unique():
            outgoing = (
                df[df["sender_id"] == sender]
                .sort_values("timestamp")
                .reset_index(drop=True)
            )
            if len(outgoing) < min_degree:
                continue

            timestamps = outgoing["timestamp"].values
            receivers = outgoing["receiver_id"].values

            for i in range(len(timestamps)):
                window_end = timestamps[i] + window
                mask = (timestamps >= timestamps[i]) & (timestamps <= window_end)
                unique_receivers = set(receivers[mask])
                if len(unique_receivers) >= min_degree:
                    self._add_flag(result, sender, "smurfing_fan_out")
                    result.clusters.append({sender} | unique_receivers)
                    logger.debug(
                        "Fan-out: %s → %d receivers", sender, len(unique_receivers)
                    )
                    break
