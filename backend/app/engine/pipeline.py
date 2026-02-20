"""
Pipeline orchestrator — single entry point for the full detection pipeline.

Execution order:
  1. Build graph (NetworkX DiGraph with node attributes)
  2. Run all three detection algorithms in sequence
  3. Merge algorithm results into combined flag map + cluster list
  4. Apply proportional suppression (payroll + merchant false-positive filters)
  5. Compute continuous suspicion scores for all flagged accounts
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
from app.engine.algorithms.velocity import VelocityAlgorithm
from app.engine.graph_builder import build_graph
from app.engine.output_builder import build_output
from app.engine.ring_merger import merge_rings
from app.engine.scoring import compute_scores
from app.engine.suppression import apply_suppression
from app.models.response import ForensicResult

logger = logging.getLogger(__name__)

# Algorithms that contribute clusters to ring detection (cycle + shell only).
# Smurfing and velocity do NOT form rings.
_RING_ALGORITHM_CLASSES = [CycleDetectionAlgorithm, ShellChainAlgorithm]
_ALL_ALGORITHM_CLASSES = [
    CycleDetectionAlgorithm,
    SmurfingAlgorithm,
    ShellChainAlgorithm,
    VelocityAlgorithm,
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
    algo_results = []
    combined_flags: dict[str, list[str]] = {}
    ring_clusters: list[set[str]] = []   # only cycle + shell contribute to rings

    for AlgoClass in _ALL_ALGORITHM_CLASSES:
        algo = AlgoClass(settings)
        r = algo.run(G, df)
        algo_results.append(r)

        for acc, patterns in r.account_flags.items():
            combined_flags.setdefault(acc, []).extend(patterns)

        # Only cycle and shell structural clusters are used for ring formation.
        if AlgoClass in _RING_ALGORITHM_CLASSES:
            ring_clusters.extend(r.clusters)

        logger.info(
            "%s: %d accounts flagged, %d clusters",
            AlgoClass.__name__,
            len(r.account_flags),
            len(r.clusters),
        )

    cycle_result, smurf_result, shell_result, velocity_result = algo_results

    # ── Step 3: Apply proportional suppression ────────────────────────────
    suppressed_flags, suppression_multipliers = apply_suppression(
        combined_flags, G, df, settings
    )
    logger.info(
        "Suppression: %d accounts with reduced scores, %d flags hidden from display",
        len(suppression_multipliers),
        sum(len(v) for v in suppressed_flags.values()),
    )

    # ── Step 4: Compute continuous scores ─────────────────────────────────
    scores = compute_scores(
        cycle_result.account_scores,
        smurf_result.account_scores,
        shell_result.account_scores,
        suppression_multipliers,
        velocity_result.account_scores,
    )
    n_above = sum(1 for s in scores.values() if s >= settings.suspicious_score_threshold)
    logger.info(
        "Scoring: %d accounts above threshold (%.1f)",
        n_above,
        settings.suspicious_score_threshold,
    )

    # ── Step 5: Merge rings (cycle + shell clusters only) ─────────────────
    rings = merge_rings(ring_clusters, scores, combined_flags, suppressed_flags, settings)
    logger.info("Rings: %d identified", len(rings))

    # ── Step 6: Build output ──────────────────────────────────────────────
    elapsed = time.perf_counter() - start
    result = build_output(
        scores, combined_flags, suppressed_flags, rings, G, df, elapsed, settings
    )

    logger.info("Pipeline complete in %.3fs", elapsed)
    return result, elapsed
