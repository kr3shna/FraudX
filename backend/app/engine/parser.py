import io
import logging

import pandas as pd

from app.models.response import ValidationSummary

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {"transaction_id", "sender_id", "receiver_id", "amount", "timestamp"}
)


def parse_csv(content: bytes) -> tuple[pd.DataFrame, ValidationSummary]:
    """
    Parse raw CSV bytes into a clean, typed DataFrame.

    Applies all validation rules in order:
      1. Parse bytes → raw DataFrame (raises ValueError on unreadable content)
      2. Normalise column names (strip + lowercase)
      3. Assert all required columns are present (raises ValueError if missing)
      4. Drop duplicate transaction_id rows (keep first occurrence)
      5. Drop self-loop rows (sender_id == receiver_id)
      6. Coerce amount → float64, drop rows where amount ≤ 0 or unparseable
      7. Parse timestamp → datetime64, drop rows where format invalid
      8. Assert at least one valid row remains (raises ValueError if empty)

    Returns:
        df               — clean DataFrame with columns:
                           transaction_id (str), sender_id (str), receiver_id (str),
                           amount (float64), timestamp (datetime64[ns])
        ValidationSummary — row counts and per-reason skip counts

    Raises:
        ValueError — for unrecoverable schema or content errors.
                     Caller (API layer) converts to the appropriate HTTP status.
    """
    # ── Step 1: Read raw bytes ────────────────────────────────────────────────
    try:
        df_raw = pd.read_csv(
            io.BytesIO(content),
            dtype=str,           # read everything as string first — we coerce later
            keep_default_na=False,
            skipinitialspace=True,
        )
    except Exception as exc:
        raise ValueError(f"Could not parse file as CSV: {exc}") from exc

    if df_raw.empty:
        raise ValueError("CSV file is empty.")

    # ── Step 2: Normalise column names ────────────────────────────────────────
    df_raw.columns = df_raw.columns.str.strip().str.lower()

    # ── Step 3: Require all columns ───────────────────────────────────────────
    missing_cols = REQUIRED_COLUMNS - set(df_raw.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

    rows_total: int = len(df_raw)
    skip_reasons: dict[str, int] = {}

    df = df_raw.copy()

    # ── Step 4: Drop duplicate transaction_id ────────────────────────────────
    dupe_mask = df.duplicated(subset=["transaction_id"], keep="first")
    n_dupes = int(dupe_mask.sum())
    if n_dupes:
        skip_reasons["duplicate_transaction_id"] = n_dupes
        df = df[~dupe_mask].copy()

    # ── Step 5: Drop self-loops ───────────────────────────────────────────────
    df["sender_id"] = df["sender_id"].str.strip()
    df["receiver_id"] = df["receiver_id"].str.strip()
    self_loop_mask = df["sender_id"] == df["receiver_id"]
    n_self_loops = int(self_loop_mask.sum())
    if n_self_loops:
        skip_reasons["self_loop"] = n_self_loops
        df = df[~self_loop_mask].copy()

    # ── Step 6: Coerce amount ─────────────────────────────────────────────────
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    invalid_amount_mask = df["amount"].isna() | (df["amount"] <= 0)
    n_invalid_amount = int(invalid_amount_mask.sum())
    if n_invalid_amount:
        skip_reasons["invalid_amount"] = n_invalid_amount
        df = df[~invalid_amount_mask].copy()

    # ── Step 7: Parse timestamp ───────────────────────────────────────────────
    df["timestamp"] = pd.to_datetime(
        df["timestamp"].str.strip(),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    invalid_ts_mask = df["timestamp"].isna()
    n_invalid_ts = int(invalid_ts_mask.sum())
    if n_invalid_ts:
        skip_reasons["invalid_timestamp"] = n_invalid_ts
        df = df[~invalid_ts_mask].copy()

    # ── Step 8: Assert non-empty ──────────────────────────────────────────────
    rows_accepted = len(df)
    if rows_accepted == 0:
        raise ValueError(
            "No valid rows remain after cleaning. "
            f"Skipped {rows_total} rows: {skip_reasons}"
        )

    # ── Finalise ──────────────────────────────────────────────────────────────
    df = df[["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"]]
    df = df.reset_index(drop=True)
    df["transaction_id"] = df["transaction_id"].str.strip()

    rows_skipped = rows_total - rows_accepted

    logger.info(
        "CSV parsed: %d total, %d accepted, %d skipped %s",
        rows_total,
        rows_accepted,
        rows_skipped,
        skip_reasons if skip_reasons else "",
    )

    return df, ValidationSummary(
        rows_total=rows_total,
        rows_accepted=rows_accepted,
        rows_skipped=rows_skipped,
        skip_reasons=skip_reasons,
    )
