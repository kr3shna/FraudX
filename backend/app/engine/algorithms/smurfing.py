"""
Smurfing detection algorithm.

Fan-in:  many unique senders → one receiver within a sliding 72-hour window.
Fan-out: one sender → many unique receivers within a sliding 72-hour window.

Strategy per direction:
  - For each candidate account, sort their transactions by timestamp.
  - Convert timestamps to int64 nanoseconds for fast numpy comparisons.
  - Use numpy.searchsorted (binary search) to find the right edge of each
    window in O(log n) instead of scanning with a boolean mask O(n).
  - Total complexity per account: O(k log k) where k = transaction count.
    Overall: O(n log n) — safe for 10k+ row datasets.

Pattern labels:
  "smurfing_fan_in"  — applied to the receiver account
  "smurfing_fan_out" — applied to the sender account

Clusters:
  fan-in:  {receiver} ∪ {all senders in the triggering window}
  fan-out: {sender}   ∪ {all receivers in the triggering window}
"""

import logging

import numpy as np
import pandas as pd
import networkx as nx

from app.models.algorithm_result import AlgorithmResult
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class SmurfingAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()
        window_ns = int(
            pd.Timedelta(hours=self.settings.smurfing_window_hours).total_seconds() * 1e9
        )
        min_degree = self.settings.smurfing_min_degree

        # Pre-group once — reused by both fan-in and fan-out
        by_receiver = df.sort_values("timestamp").groupby("receiver_id", sort=False)
        by_sender   = df.sort_values("timestamp").groupby("sender_id",   sort=False)

        self._detect_fan_in( by_receiver, result, window_ns, min_degree)
        self._detect_fan_out(by_sender,   result, window_ns, min_degree)

        logger.info(
            "SmurfingDetection: %d accounts flagged, %d clusters",
            len(result.account_flags),
            len(result.clusters),
        )
        return result

    # ── Fan-in ────────────────────────────────────────────────────────────

    def _detect_fan_in(self, by_receiver, result, window_ns: int, min_degree: int) -> None:
        for receiver, group in by_receiver:
            if len(group) < min_degree:
                continue

            ts      = group["timestamp"].values.astype(np.int64)
            senders = group["sender_id"].values

            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                unique_senders = set(senders[i:right])
                if len(unique_senders) >= min_degree:
                    self._add_flag(result, receiver, "smurfing_fan_in")
                    result.clusters.append({receiver} | unique_senders)
                    logger.debug("Fan-in: %s ← %d senders", receiver, len(unique_senders))
                    break

    # ── Fan-out ───────────────────────────────────────────────────────────

    def _detect_fan_out(self, by_sender, result, window_ns: int, min_degree: int) -> None:
        for sender, group in by_sender:
            if len(group) < min_degree:
                continue

            ts        = group["timestamp"].values.astype(np.int64)
            receivers = group["receiver_id"].values

            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                unique_receivers = set(receivers[i:right])
                if len(unique_receivers) >= min_degree:
                    self._add_flag(result, sender, "smurfing_fan_out")
                    result.clusters.append({sender} | unique_receivers)
                    logger.debug("Fan-out: %s → %d receivers", sender, len(unique_receivers))
                    break
