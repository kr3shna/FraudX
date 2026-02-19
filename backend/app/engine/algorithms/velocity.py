"""
Velocity analysis algorithm.

Detects accounts with abnormal transaction rate patterns:

  burst_activity  — 5+ outgoing transactions in a 1-hour window
  high_velocity   — 15+ outgoing transactions in a 24-hour window
  velocity_spike  — last 7-day outgoing rate is 3× the previous 7-day rate
  dormancy_break  — account inactive (all directions) 30+ days, then 5+ txns
                    in the following 48 hours

Pattern labels:
  "burst_activity"  — rapid concentrated sending
  "high_velocity"   — sustained high outgoing rate
  "velocity_spike"  — sudden rate acceleration
  "dormancy_break"  — reactivation after long inactivity

Continuous score sub-factors:
  burst_activity / high_velocity:
    f_count (60%) — how many txns above min threshold (2× min → 1.0)
    f_speed (40%) — how concentrated: instantaneous → 1.0, full window → 0
  velocity_spike:
    f_ratio (100%) — how far above spike_ratio threshold (capped at 2× spike_ratio)
  dormancy_break:
    f_dormancy (50%) — gap length; 90+ days → 1.0
    f_burst    (50%) — post-gap burst intensity; 2× threshold → 1.0

No clusters are produced — velocity accounts never form rings.
Maximum category score: 15.0
"""

import logging

import networkx as nx
import numpy as np
import pandas as pd

from app.models.algorithm_result import AlgorithmResult

from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class VelocityAlgorithm(BaseAlgorithm):

    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        # Pre-sort once; groupby with sort=False preserves within-group order.
        df_sorted = df.sort_values("timestamp")
        by_sender = df_sorted.groupby("sender_id", sort=False)

        # Per-account combined sorted int64-ns timestamp arrays (sent + received).
        all_by_account = self._build_all_account_ts(df_sorted)

        self._detect_burst(by_sender, result)
        self._detect_high_velocity(by_sender, result)
        self._detect_velocity_spike(by_sender, result)
        self._detect_dormancy_break(all_by_account, result)

        logger.info(
            "VelocityAlgorithm: %d accounts flagged, 0 clusters",
            len(result.account_flags),
        )
        return result

    # ── Data preparation ───────────────────────────────────────────────────

    @staticmethod
    def _build_all_account_ts(df_sorted: pd.DataFrame) -> dict[str, np.ndarray]:
        """Return per-account sorted int64-ns timestamp arrays (sent + received)."""
        sender_ts: dict[str, np.ndarray] = {
            s: g["timestamp"].values.astype(np.int64)
            for s, g in df_sorted.groupby("sender_id", sort=False)
        }
        receiver_ts: dict[str, np.ndarray] = {
            r: g["timestamp"].values.astype(np.int64)
            for r, g in df_sorted.groupby("receiver_id", sort=False)
        }
        combined: dict[str, np.ndarray] = {}
        for acc in set(sender_ts) | set(receiver_ts):
            parts = []
            if acc in sender_ts:
                parts.append(sender_ts[acc])
            if acc in receiver_ts:
                parts.append(receiver_ts[acc])
            arr = np.concatenate(parts)
            arr.sort()
            combined[acc] = arr
        return combined

    # ── Pattern: burst_activity ────────────────────────────────────────────

    def _detect_burst(self, by_sender, result: AlgorithmResult) -> None:
        min_txns = self.settings.burst_min_transactions
        window_ns = int(
            pd.Timedelta(hours=self.settings.burst_window_hours).total_seconds() * 1e9
        )
        for sender, group in by_sender:
            ts = group["timestamp"].values.astype(np.int64)
            if len(ts) < min_txns:
                continue
            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                count = right - i
                if count >= min_txns:
                    span_ns = int(ts[right - 1] - ts[i])
                    score = self._score_window(count, span_ns, window_ns, min_txns)
                    self._add_flag(result, sender, "burst_activity")
                    if result.account_scores.get(sender, 0.0) < score:
                        result.account_scores[sender] = score
                    break  # worst window found; move to next sender

    # ── Pattern: high_velocity ─────────────────────────────────────────────

    def _detect_high_velocity(self, by_sender, result: AlgorithmResult) -> None:
        min_txns = self.settings.daily_velocity_min_transactions
        window_ns = int(
            pd.Timedelta(hours=self.settings.daily_velocity_window_hours).total_seconds() * 1e9
        )
        for sender, group in by_sender:
            ts = group["timestamp"].values.astype(np.int64)
            if len(ts) < min_txns:
                continue
            for i in range(len(ts)):
                right = int(np.searchsorted(ts, ts[i] + window_ns, side="right"))
                count = right - i
                if count >= min_txns:
                    span_ns = int(ts[right - 1] - ts[i])
                    score = self._score_window(count, span_ns, window_ns, min_txns)
                    self._add_flag(result, sender, "high_velocity")
                    if result.account_scores.get(sender, 0.0) < score:
                        result.account_scores[sender] = score
                    break

    # ── Pattern: velocity_spike ────────────────────────────────────────────

    def _detect_velocity_spike(self, by_sender, result: AlgorithmResult) -> None:
        spike_ratio = self.settings.velocity_spike_ratio
        window_ns = int(
            pd.Timedelta(days=self.settings.velocity_spike_window_days).total_seconds() * 1e9
        )
        for sender, group in by_sender:
            ts = group["timestamp"].values.astype(np.int64)
            if len(ts) < 2:
                continue

            latest = ts[-1]
            current_start = latest - window_ns
            current_count = len(ts) - int(np.searchsorted(ts, current_start, side="left"))

            prev_end = current_start
            prev_start = prev_end - window_ns
            prev_lo = int(np.searchsorted(ts, prev_start, side="left"))
            prev_hi = int(np.searchsorted(ts, prev_end, side="left"))  # exclude boundary
            prev_count = prev_hi - prev_lo

            if prev_count == 0:
                continue  # no prior history to compare against

            ratio = current_count / prev_count
            if ratio >= spike_ratio:
                f_ratio = min(1.0, (ratio - spike_ratio) / spike_ratio)
                score = round(15.0 * f_ratio, 2)
                self._add_flag(result, sender, "velocity_spike")
                if result.account_scores.get(sender, 0.0) < score:
                    result.account_scores[sender] = score

    # ── Pattern: dormancy_break ────────────────────────────────────────────

    def _detect_dormancy_break(
        self, all_by_account: dict[str, np.ndarray], result: AlgorithmResult
    ) -> None:
        dormancy_ns = int(
            pd.Timedelta(days=self.settings.dormancy_min_days).total_seconds() * 1e9
        )
        activity_ns = int(
            pd.Timedelta(hours=self.settings.dormancy_activity_window_hours).total_seconds() * 1e9
        )
        threshold = self.settings.dormancy_activity_threshold

        for acc, ts in all_by_account.items():
            if len(ts) < 2:
                continue

            gaps = np.diff(ts)
            max_gap_idx = int(np.argmax(gaps))
            max_gap_ns = int(gaps[max_gap_idx])

            if max_gap_ns < dormancy_ns:
                continue

            # Count all transactions in the activity window immediately after the gap
            resume_ts = int(ts[max_gap_idx + 1])
            post_gap_count = (
                int(np.searchsorted(ts, resume_ts + activity_ns, side="right"))
                - (max_gap_idx + 1)
            )

            if post_gap_count >= threshold:
                self._add_flag(result, acc, "dormancy_break")
                gap_days = max_gap_ns / (1e9 * 86400)
                f_dormancy = min(1.0, gap_days / 90.0)
                f_burst = min(
                    1.0,
                    (post_gap_count - threshold) / max(1, threshold),
                )
                raw = 0.50 * f_dormancy + 0.50 * f_burst
                score = round(15.0 * raw, 2)
                if result.account_scores.get(acc, 0.0) < score:
                    result.account_scores[acc] = score

    # ── Shared scoring helper ──────────────────────────────────────────────

    @staticmethod
    def _score_window(count: int, span_ns: int, window_ns: int, min_txns: int) -> float:
        """Score a sliding-window hit for burst_activity / high_velocity."""
        # f_count: 0 at min_txns, 1.0 at 2× min_txns
        f_count = min(1.0, (count - min_txns) / max(1, min_txns))
        # f_speed: instantaneous (span=0) → 1.0; full window used → 0
        f_speed = 1.0 - min(1.0, span_ns / max(1, window_ns))
        return round(15.0 * (0.60 * f_count + 0.40 * f_speed), 2)
