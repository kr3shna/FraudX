"""POST /api/analyze — upload a CSV, run the full pipeline, return the result."""

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import Settings, settings
from app.engine.parser import parse_csv
from app.engine.pipeline import run_pipeline
from app.models.response import AnalyzeResponse
from app.store.memory_store import MemoryStore, get_store

router = APIRouter()
logger = logging.getLogger(__name__)

# Hard row limit applied after parsing — prevents slow algorithms on huge datasets.
_MAX_ROWS = 15_000


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    store: MemoryStore = Depends(get_store),
    cfg: Settings = Depends(lambda: settings),
) -> AnalyzeResponse:
    req_id = getattr(request.state, "request_id", "unknown")
    logger.info("[%s] Received upload: %s", req_id, file.filename)

    # ── 1. File-type guard ────────────────────────────────────────────────
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="File must be a CSV (.csv)")

    # ── 2. Read & size guard ──────────────────────────────────────────────
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > cfg.max_upload_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {cfg.max_upload_size_mb} MB limit "
                   f"(received {size_mb:.1f} MB)",
        )

    # ── 3. Parse & validate ───────────────────────────────────────────────
    try:
        df, validation_summary = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ── 4. Row-count guard ────────────────────────────────────────────────
    if len(df) > _MAX_ROWS:
        raise HTTPException(
            status_code=422,
            detail=f"Dataset too large: {len(df):,} rows (max {_MAX_ROWS:,})",
        )

    # ── 5. Run pipeline ───────────────────────────────────────────────────
    result, elapsed = run_pipeline(df, cfg)
    logger.info(
        "[%s] Pipeline complete in %.3fs — %d suspicious accounts, %d rings",
        req_id,
        elapsed,
        result.summary.suspicious_accounts_flagged,
        result.summary.fraud_rings_detected,
    )

    # ── 6. Persist result & return ────────────────────────────────────────
    session_token = uuid.uuid4().hex[:12]
    store.set(session_token, result)

    return AnalyzeResponse(
        status="success",
        session_token=session_token,
        validation_summary=validation_summary,
        result=result,
    )
