"""Unit tests for app/engine/parser.py."""
import io
import pathlib
import textwrap

import pandas as pd
import pytest

from app.engine.parser import parse_csv

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


def _csv(text: str) -> bytes:
    """Strip leading indentation and encode as UTF-8 bytes."""
    return textwrap.dedent(text).strip().encode()


# ── 1. Happy path ────────────────────────────────────────────────────────────

def test_triangle_cycle_happy_path():
    content = (FIXTURES / "triangle_cycle.csv").read_bytes()
    df, summary = parse_csv(content)

    assert summary.rows_total == 3
    assert summary.rows_accepted == 3
    assert summary.rows_skipped == 0
    assert summary.skip_reasons == {}

    assert list(df.columns) == [
        "transaction_id", "sender_id", "receiver_id", "amount", "timestamp"
    ]
    assert len(df) == 3


# ── 2. Missing required column ───────────────────────────────────────────────

def test_missing_column_raises():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount
        T001,ACC_A,ACC_B,100.00
    """)
    with pytest.raises(ValueError, match="Missing required columns"):
        parse_csv(content)


# ── 3. Duplicate transaction_id ──────────────────────────────────────────────

def test_duplicate_transaction_id_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,100.00,2024-01-01 10:00:00
        T001,ACC_A,ACC_C,200.00,2024-01-01 11:00:00
        T002,ACC_A,ACC_D,300.00,2024-01-01 12:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_total == 3
    assert summary.rows_accepted == 2
    assert summary.rows_skipped == 1
    assert summary.skip_reasons["duplicate_transaction_id"] == 1
    # First occurrence kept: receiver ACC_B, not ACC_C
    assert df.iloc[0]["receiver_id"] == "ACC_B"


# ── 4. Self-loop (sender == receiver) ────────────────────────────────────────

def test_self_loop_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_A,100.00,2024-01-01 10:00:00
        T002,ACC_A,ACC_B,200.00,2024-01-01 11:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert summary.skip_reasons["self_loop"] == 1
    assert df.iloc[0]["transaction_id"] == "T002"


# ── 5. Invalid amount ────────────────────────────────────────────────────────

def test_negative_amount_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,-50.00,2024-01-01 10:00:00
        T002,ACC_A,ACC_B,100.00,2024-01-01 11:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert summary.skip_reasons["invalid_amount"] == 1


def test_zero_amount_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,0.00,2024-01-01 10:00:00
        T002,ACC_A,ACC_B,100.00,2024-01-01 11:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert summary.skip_reasons["invalid_amount"] == 1


def test_non_numeric_amount_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,not_a_number,2024-01-01 10:00:00
        T002,ACC_A,ACC_B,100.00,2024-01-01 11:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert summary.skip_reasons["invalid_amount"] == 1


# ── 6. Invalid timestamp ─────────────────────────────────────────────────────

def test_invalid_timestamp_skipped():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,100.00,not-a-date
        T002,ACC_A,ACC_B,200.00,2024-01-01 10:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert summary.skip_reasons["invalid_timestamp"] == 1


# ── 7. All rows invalid ──────────────────────────────────────────────────────

def test_all_rows_invalid_raises():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_A,100.00,2024-01-01 10:00:00
        T002,ACC_B,ACC_B,200.00,2024-01-01 11:00:00
    """)
    with pytest.raises(ValueError, match="No valid rows"):
        parse_csv(content)


# ── 8. Empty CSV ─────────────────────────────────────────────────────────────

def test_empty_csv_raises():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
    """)
    with pytest.raises(ValueError, match="empty"):
        parse_csv(content)


def test_totally_empty_bytes_raises():
    with pytest.raises(ValueError):
        parse_csv(b"")


# ── 9. Column names with extra whitespace ────────────────────────────────────

def test_column_whitespace_normalized():
    content = _csv("""
        transaction_id , sender_id , receiver_id , amount , timestamp
        T001,ACC_A,ACC_B,100.00,2024-01-01 10:00:00
    """)
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 1
    assert "amount" in df.columns


# ── 10. Amount coerced to float64 ────────────────────────────────────────────

def test_amount_dtype_float64():
    content = _csv("""
        transaction_id,sender_id,receiver_id,amount,timestamp
        T001,ACC_A,ACC_B,100,2024-01-01 10:00:00
        T002,ACC_A,ACC_C,200.50,2024-01-01 11:00:00
    """)
    df, _ = parse_csv(content)

    assert df["amount"].dtype == "float64"


# ── 11. fan_in_smurfing.csv → 12 rows accepted ───────────────────────────────

def test_fan_in_smurfing_fixture():
    content = (FIXTURES / "fan_in_smurfing.csv").read_bytes()
    df, summary = parse_csv(content)

    assert summary.rows_accepted == 12
    assert summary.rows_skipped == 0
    assert df["receiver_id"].nunique() == 1
    assert df["sender_id"].nunique() == 12
