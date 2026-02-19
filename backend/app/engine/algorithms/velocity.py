"""
Velocity analysis algorithm.

Detects four temporal anomaly patterns (all based on sender activity):

  burst_activity   — ≥ burst_min_transactions unique send events within
                     burst_window_hours (default: 5 in 1 hour)

  high_velocity    — ≥ daily_velocity_min_transactions send events within
                     daily_velocity_window_hours (default: 15 in 24 hours)

  velocity_spike   — peak daily count > velocity_spike_ratio × mean daily
                     count over the preceding velocity_spike_window_days days
                     (requires at least 2 active days in baseline)

  dormancy_break   — gap of ≥ dormancy_min_days between consecutive
                     transactions, followed by ≥ dormancy_activity_threshold
                     transactions within dormancy_activity_window_hours

Pattern labels:
  "burst_activity" | "high_velocity" | "velocity_spike" | "dormancy_break"

No clusters are produced: velocity patterns are account-level, not network-level.
"""

import logging

import pandas as pd

from app.models.algorithm_result import AlgorithmResult
import networkx as nx
from .base import BaseAlgorithm

logger = logging.getLogger(__name__)


class VelocityAlgorithm(BaseAlgorithm):
    def run(self, G: nx.DiGraph, df: pd.DataFrame) -> AlgorithmResult:
        result = AlgorithmResult()

        for sender in df["sender_id"].unique():
            txns = (
                df[df["sender_id"] == sender]
                .sort_values("timestamp")
                .reset_index(drop=True)
            )
            timestamps = txns["timestamp"]

            if self._is_burst(timestamps):
                self._add_flag(result, sender, "burst_activity")
                logger.debug("burst_activity: %s", sender)

            if self._is_high_velocity(timestamps):
                self._add_flag(result, sender, "high_velocity")
                logger.debug("high_velocity: %s", sender)

            if self._is_velocity_spike(timestamps):
                self._add_flag(result, sender, "velocity_spike")
                logger.debug("velocity_spike: %s", sender)

            if self._is_dormancy_break(timestamps):
                self._add_flag(result, sender, "dormancy_break")
                logger.debug("dormancy_break: %s", sender)

        logger.info(
            "VelocityAnalysis: %d accounts flagged", len(result.account_flags)
        )
        return result

    # ── Burst activity ────────────────────────────────────────────────────

    def _is_burst(self, timestamps: pd.Series) -> bool:
        n = self.settings.burst_min_transactions
        window = pd.Timedelta(hours=self.settings.burst_window_hours)
        if len(timestamps) < n:
            return False
        ts = timestamps.values
        for i in range(len(ts)):
            count = int(((ts >= ts[i]) & (ts <= ts[i] + window)).sum())
            if count >= n:
                return True
        return False

    # ── High velocity ─────────────────────────────────────────────────────

    def _is_high_velocity(self, timestamps: pd.Series) -> bool:
        n = self.settings.daily_velocity_min_transactions
        window = pd.Timedelta(hours=self.settings.daily_velocity_window_hours)
        if len(timestamps) < n:
            return False
        ts = timestamps.values
        for i in range(len(ts)):
            count = int(((ts >= ts[i]) & (ts <= ts[i] + window)).sum())
            if count >= n:
                return True
        return False

    # ── Velocity spike ────────────────────────────────────────────────────

    def _is_velocity_spike(self, timestamps: pd.Series) -> bool:
        if len(timestamps) < 2:
            return False

        ratio = self.settings.velocity_spike_ratio
        baseline_days = self.settings.velocity_spike_window_days

        # Group transaction counts by calendar day
        days = timestamps.dt.floor("D")
        daily_counts = days.value_counts().sort_index()

        if len(daily_counts) < 2:
            return False

        baseline_window = pd.Timedelta(days=baseline_days)

        for i, (day, count) in enumerate(daily_counts.items()):
            # Baseline: daily counts in the preceding baseline_days
            baseline_start = day - baseline_window
            baseline = daily_counts[
                (daily_counts.index >= baseline_start) & (daily_counts.index < day)
            ]
            if len(baseline) < 1:
                continue
            baseline_mean = baseline.mean()
            if baseline_mean > 0 and count > ratio * baseline_mean:
                return True

        return False

    # ── Dormancy break ────────────────────────────────────────────────────

    def _is_dormancy_break(self, timestamps: pd.Series) -> bool:
        if len(timestamps) < 2:
            return False

        dormancy_gap = pd.Timedelta(days=self.settings.dormancy_min_days)
        activity_window = pd.Timedelta(
            hours=self.settings.dormancy_activity_window_hours
        )
        threshold = self.settings.dormancy_activity_threshold

        ts = timestamps.sort_values().reset_index(drop=True)

        for i in range(1, len(ts)):
            gap = ts[i] - ts[i - 1]
            if gap >= dormancy_gap:
                # Count activity in the window after the gap
                post_gap_start = ts[i]
                post_gap_end = post_gap_start + activity_window
                post_count = int(
                    ((ts >= post_gap_start) & (ts <= post_gap_end)).sum()
                )
                if post_count >= threshold:
                    return True

        return False
