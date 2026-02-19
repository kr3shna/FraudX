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

Continuous score sub-factors (weights):
  f_degree      (35%) — how many unique counterparties in the window
  f_speed       (30%) — how fast they arrived (fraction of 72h window used)
  f_volume      (20%) — total $ aggregated in the window vs dataset median
  f_uniformity  (15%) — how similar the amounts are; low CV = structured smurfing

Clusters:
  fan-in:  {receiver} ∪ {all senders in the triggering window}
  fan-out: {sender}   ∪ {all receivers in the triggering window}
"""

import logging
import math

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
        median_amount = float(df["amount"].median())

        # Pre-group once — reused by both fan-in and fan-out
        by_receiver = df.sort_values("timestamp").groupby("receiver_id", sort=False)
        by_sender   = df.sort_values("timestamp").groupby("sender_id",   sort=False)

        self._detect_fan_in( by_receiver, result, window_ns, min_degree, median_amount)
        self._detect_fan_out(by_sender,   result, window_ns, min_degree, median_amount)

        logger.info(
            "SmurfingDetection: %d accounts flagged, %d clusters",
            len(result.account_flags),
            len(result.clusters),
        )
        return result

    # ── Fan-in ────────────────────────────────────────────────────────────

    def _detect_fan_in(
        self, by_receiver, result, window_ns: int, min_degree: int, median_amount: float
    ) -> None:
        for receiver, group in by_receiver:
            if len(group) < min_degree:
                continue

            ts      = group["timestamp"].values.astype(np.int64)
            senders = group["sender_id"].values
            amounts = group["amount"].values

            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                unique_senders = set(senders[i:right])
                if len(unique_senders) >= min_degree:
                    self._add_flag(result, receiver, "smurfing_fan_in")
                    result.clusters.append({receiver} | unique_senders)

                    actual_window_ns = int(ts[min(right - 1, len(ts) - 1)] - ts[i])
                    score = self._score_smurfing(
                        unique_count=len(unique_senders),
                        actual_window_ns=actual_window_ns,
                        max_window_ns=window_ns,
                        window_amounts=amounts[i:right],
                        median_amount=median_amount,
                        min_degree=min_degree,
                    )
                    if result.account_scores.get(receiver, 0.0) < score:
                        result.account_scores[receiver] = score

                    logger.debug("Fan-in: %s ← %d senders", receiver, len(unique_senders))
                    break

    # ── Fan-out ───────────────────────────────────────────────────────────

    def _detect_fan_out(
        self, by_sender, result, window_ns: int, min_degree: int, median_amount: float
    ) -> None:
        for sender, group in by_sender:
            if len(group) < min_degree:
                continue

            ts        = group["timestamp"].values.astype(np.int64)
            receivers = group["receiver_id"].values
            amounts   = group["amount"].values

            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                unique_receivers = set(receivers[i:right])
                if len(unique_receivers) >= min_degree:
                    self._add_flag(result, sender, "smurfing_fan_out")
                    result.clusters.append({sender} | unique_receivers)

                    actual_window_ns = int(ts[min(right - 1, len(ts) - 1)] - ts[i])
                    score = self._score_smurfing(
                        unique_count=len(unique_receivers),
                        actual_window_ns=actual_window_ns,
                        max_window_ns=window_ns,
                        window_amounts=amounts[i:right],
                        median_amount=median_amount,
                        min_degree=min_degree,
                    )
                    if result.account_scores.get(sender, 0.0) < score:
                        result.account_scores[sender] = score

                    logger.debug("Fan-out: %s → %d receivers", sender, len(unique_receivers))
                    break

    # ── Continuous scoring ────────────────────────────────────────────────

    def _score_smurfing(
        self,
        unique_count: int,
        actual_window_ns: int,
        max_window_ns: int,
        window_amounts: np.ndarray,
        median_amount: float,
        min_degree: int,
    ) -> float:
        # f_degree: more unique counterparties beyond minimum → more suspicious
        # 40+ unique above threshold → 1.0
        f_degree = min(1.0, (unique_count - min_degree) / max(1, 40 - min_degree))

        # f_speed: fraction of window actually used; instantaneous = 1.0
        if max_window_ns > 0:
            f_speed = 1.0 - min(1.0, actual_window_ns / max_window_ns)
        else:
            f_speed = 1.0

        # f_volume: total $ in window vs dataset median; 10000× median → 1.0
        total_volume = float(window_amounts.sum()) if len(window_amounts) > 0 else 0.0
        if median_amount > 0:
            f_volume = min(1.0, math.log10(max(1.0, total_volume / median_amount)) / 4.0)
        else:
            f_volume = 0.0

        # f_uniformity: low CV = structured amounts (classic structuring)
        if len(window_amounts) > 1:
            mean_amt = float(window_amounts.mean())
            if mean_amt > 0:
                cv = float(window_amounts.std()) / mean_amt
                f_uniformity = max(0.0, 1.0 - cv / 0.5)
            else:
                f_uniformity = 0.0
        else:
            f_uniformity = 0.0

        raw = (
            0.35 * f_degree
            + 0.30 * f_speed
            + 0.20 * f_volume
            + 0.15 * f_uniformity
        )
        return round(25.0 * raw, 2)
