"""
Pipeline orchestrator — single entry point for the full detection pipeline.

Execution order:
  1. Build graph (NetworkX DiGraph with node attributes)
  2. Run all three detection algorithms in sequence
  3. Merge algorithm results into combined flag map + cluster list
  4. Apply suppression rules (payroll + merchant false-positive filters)
  5. Compute suspicion scores for all flagged accounts
  6. Merge clusters into named rings via Union-Find
  7. Build and return the ForensicResult
"""

import logging
import time

import pandas as pd

from app.config import Settings
from app.engine.algorithms.cycle_detection import CycleDetectionAlgorithm
from app.engine.algorithms.shell_chain import ShellChainAlgorithm
from app.engine.algorithms.smurfing import SmurfingAlgorithm
from app.engine.graph_builder import build_graph
from app.engine.output_builder import build_output
from app.engine.ring_merger import merge_rings
from app.engine.scoring import compute_scores
from app.engine.suppression import apply_suppression
from app.models.response import ForensicResult

logger = logging.getLogger(__name__)

_ALGORITHM_CLASSES = [
    CycleDetectionAlgorithm,
    SmurfingAlgorithm,
    ShellChainAlgorithm,
]


def run_pipeline(
    df: pd.DataFrame,
    settings: Settings,
) -> tuple[ForensicResult, float]:
    """
    Run the full forensic analysis pipeline.

    Args:
        df:       Clean, typed transaction DataFrame from parse_csv().
        settings: Application settings (algorithm thresholds, etc.).

    Returns:
        (ForensicResult, processing_time_seconds)
    """
    start = time.perf_counter()

    unique_accounts = df["sender_id"].nunique() + df["receiver_id"].nunique()
    logger.info(
        "Pipeline start: %d transactions, ~%d unique accounts",
        len(df),
        unique_accounts,
    )

    # ── Step 1: Build graph ───────────────────────────────────────────────
    G = build_graph(df)
    logger.info("Graph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())

    # ── Step 2: Run detection algorithms ─────────────────────────────────
    combined_flags: dict[str, list[str]] = {}
    all_clusters: list[set[str]] = []

    for AlgoClass in _ALGORITHM_CLASSES:
        algo = AlgoClass(settings)
        algo_result = algo.run(G, df)

        for acc, patterns in algo_result.account_flags.items():
            combined_flags.setdefault(acc, []).extend(patterns)
        all_clusters.extend(algo_result.clusters)

        logger.info(
            "%s: %d accounts flagged, %d clusters",
            AlgoClass.__name__,
            len(algo_result.account_flags),
            len(algo_result.clusters),
        )

    # ── Step 3: Apply suppression ─────────────────────────────────────────
    suppressed_flags = apply_suppression(combined_flags, G, df, settings)
    total_suppressed = sum(len(v) for v in suppressed_flags.values())
    logger.info("Suppression: %d flags removed", total_suppressed)

    # ── Step 4: Score all accounts ────────────────────────────────────────
    scores = compute_scores(combined_flags, suppressed_flags, G, settings)
    n_above_threshold = sum(
        1 for s in scores.values() if s > settings.suspicious_score_threshold
    )
    logger.info(
        "Scoring: %d accounts above threshold (%.1f)",
        n_above_threshold,
        settings.suspicious_score_threshold,
    )

    # ── Step 5: Merge rings ───────────────────────────────────────────────
    rings = merge_rings(all_clusters, scores, combined_flags, suppressed_flags, settings)
    logger.info("Rings: %d identified", len(rings))

    # ── Step 6: Build output ──────────────────────────────────────────────
    elapsed = time.perf_counter() - start
    result = build_output(
        scores, combined_flags, suppressed_flags, rings, G, elapsed, settings
    )

    logger.info("Pipeline complete in %.3fs", elapsed)
    return result, elapsed
