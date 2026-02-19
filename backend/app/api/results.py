"""GET /api/results — retrieve and optionally filter a stored forensic result."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.middleware.rate_limiter import limiter
from app.models.response import ForensicResult, ForensicSummary
from app.store.memory_store import MemoryStore, get_store

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/results", response_model=ForensicResult)
@limiter.limit("60/minute")
async def get_results(
    request: Request,
    x_session_token: str = Header(alias="X-Session-Token"),
    account_id: str | None = Query(default=None, description="Filter to a single account"),
    ring_id: str | None = Query(default=None, description="Filter to a specific ring"),
    min_score: float | None = Query(default=None, ge=0.0, le=100.0, description="Minimum suspicion score"),
    pattern: str | None = Query(default=None, description="Filter to accounts with this pattern label"),
    store: MemoryStore = Depends(get_store),
) -> ForensicResult:
    # ── 1. Look up session ────────────────────────────────────────────────
    result = store.get(x_session_token)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    logger.info(
        "GET /results token=%s filters: account_id=%s ring_id=%s min_score=%s pattern=%s",
        x_session_token,
        account_id,
        ring_id,
        min_score,
        pattern,
    )

    # ── 2. Filter suspicious_accounts ─────────────────────────────────────
    accounts = result.suspicious_accounts

    if account_id is not None:
        accounts = [a for a in accounts if a.account_id == account_id]

    if ring_id is not None:
        accounts = [a for a in accounts if a.ring_id == ring_id]

    if min_score is not None:
        accounts = [a for a in accounts if a.suspicion_score >= min_score]

    if pattern is not None:
        accounts = [a for a in accounts if pattern in a.detected_patterns]

    # ── 3. Filter fraud_rings ─────────────────────────────────────────────
    rings = result.fraud_rings

    if ring_id is not None:
        rings = [r for r in rings if r.ring_id == ring_id]

    # ── 4. Return filtered result with original summary ───────────────────
    # Summary always reflects the full unfiltered analysis, not the filtered view.
    return ForensicResult(
        suspicious_accounts=accounts,
        fraud_rings=rings,
        summary=result.summary,
    )
