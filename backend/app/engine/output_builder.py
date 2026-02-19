"""
Output builder — assembles the final ForensicResult from all pipeline outputs.

Ordering guarantees (strictly enforced here):
  suspicious_accounts → sorted by suspicion_score DESC (ties: account_id ASC)
  fraud_rings         → sorted by risk_score DESC (ties: ring_id ASC)
  member_accounts     → sorted alphabetically per ring
  detected_patterns   → sorted alphabetically per account
"""

import networkx as nx

from app.config import Settings
from app.engine.ring_merger import RingInfo
from app.models.response import (
    ForensicResult,
    ForensicSummary,
    FraudRing,
    SuspiciousAccount,
)


def build_output(
    scores: dict[str, float],
    combined_flags: dict[str, list[str]],
    suppressed_flags: dict[str, list[str]],
    rings: list[RingInfo],
    G: nx.DiGraph,
    elapsed_seconds: float,
    settings: Settings,
) -> ForensicResult:
    """
    Produce the ForensicResult from scored accounts and merged rings.

    Only accounts with score > suspicious_score_threshold appear in output.
    """
    threshold = settings.suspicious_score_threshold

    # ── Build ring_id lookup ───────────────────────────────────────────────
    account_to_ring: dict[str, str] = {}
    for ring in rings:
        for acc in ring.member_accounts:
            account_to_ring[acc] = ring.ring_id

    # ── Build suspicious_accounts ──────────────────────────────────────────
    suspicious_accounts: list[SuspiciousAccount] = []
    for acc, score in scores.items():
        if score <= threshold:
            continue

        removed = set(suppressed_flags.get(acc, []))
        effective_patterns = sorted(
            p for p in combined_flags.get(acc, []) if p not in removed
        )

        suspicious_accounts.append(
            SuspiciousAccount(
                account_id=acc,
                suspicion_score=round(score, 2),
                detected_patterns=effective_patterns,
                ring_id=account_to_ring.get(acc, "NONE"),
            )
        )

    # Sort: score DESC, then account_id ASC for determinism
    suspicious_accounts.sort(key=lambda a: (-a.suspicion_score, a.account_id))

    # ── Build fraud_rings ──────────────────────────────────────────────────
    fraud_rings: list[FraudRing] = [
        FraudRing(
            ring_id=ring.ring_id,
            member_accounts=ring.member_accounts,  # already sorted by ring_merger
            pattern_type=ring.pattern_type,
            risk_score=ring.risk_score,
        )
        for ring in rings
    ]
    # Sort: risk_score DESC, then ring_id ASC for determinism
    fraud_rings.sort(key=lambda r: (-r.risk_score, r.ring_id))

    # ── Build summary ──────────────────────────────────────────────────────
    total_accounts = G.number_of_nodes()
    summary = ForensicSummary(
        total_accounts_analyzed=total_accounts,
        suspicious_accounts_flagged=len(suspicious_accounts),
        fraud_rings_detected=len(fraud_rings),
        processing_time_seconds=round(elapsed_seconds, 4),
    )

    return ForensicResult(
        suspicious_accounts=suspicious_accounts,
        fraud_rings=fraud_rings,
        summary=summary,
    )
