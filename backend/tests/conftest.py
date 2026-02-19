"""Shared pytest fixtures used across unit and integration tests."""

import pathlib

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.engine.graph_builder import build_graph
from app.store.memory_store import reset_store
from main import app

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


# ── Settings ──────────────────────────────────────────────────────────────────

@pytest.fixture
def settings() -> Settings:
    return Settings()


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """TestClient with a fresh MemoryStore for every test."""
    reset_store()
    with TestClient(app) as c:
        yield c
    reset_store()


# ── DataFrames ────────────────────────────────────────────────────────────────

@pytest.fixture
def triangle_df() -> pd.DataFrame:
    return pd.DataFrame({
        "transaction_id": ["T001", "T002", "T003"],
        "sender_id":      ["ACC_A", "ACC_B", "ACC_C"],
        "receiver_id":    ["ACC_B", "ACC_C", "ACC_A"],
        "amount":         [5000.0, 4800.0, 4600.0],
        "timestamp":      pd.to_datetime([
            "2024-01-01 10:00:00",
            "2024-01-01 11:00:00",
            "2024-01-01 12:00:00",
        ]),
    })


@pytest.fixture
def fan_in_df() -> pd.DataFrame:
    """12 unique senders → ACC_RECV within 11 hours."""
    senders = [f"ACC_S{i:02d}" for i in range(1, 13)]
    return pd.DataFrame({
        "transaction_id": [f"FI{i:03d}" for i in range(1, 13)],
        "sender_id":      senders,
        "receiver_id":    ["ACC_RECV"] * 12,
        "amount":         [float(950 + i * 5) for i in range(12)],
        "timestamp":      pd.to_datetime([
            f"2024-01-01 {8 + i}:00:00" for i in range(12)
        ]),
    })


@pytest.fixture
def fan_out_df() -> pd.DataFrame:
    """ACC_SEND → 12 unique receivers within 5.5 hours."""
    receivers = [f"ACC_R{i:02d}" for i in range(1, 13)]
    return pd.DataFrame({
        "transaction_id": [f"FO{i:03d}" for i in range(1, 13)],
        "sender_id":      ["ACC_SEND"] * 12,
        "receiver_id":    receivers,
        "amount":         [float(950 + i * 5) for i in range(12)],
        "timestamp":      pd.to_datetime([
            f"2024-01-01 {8}:{i * 30 % 60}:{(i * 30) // 60 * 10}" for i in range(12)
        ]),
    })


@pytest.fixture
def payroll_df() -> pd.DataFrame:
    """ACC_EMPLOYER → 20 receivers, all 1200.00, 6-min intervals (payroll pattern)."""
    receivers = [f"ACC_R{i:02d}" for i in range(1, 21)]
    base = pd.Timestamp("2024-01-01 09:00:00")
    return pd.DataFrame({
        "transaction_id": [f"PR{i:03d}" for i in range(1, 21)],
        "sender_id":      ["ACC_EMPLOYER"] * 20,
        "receiver_id":    receivers,
        "amount":         [1200.0] * 20,
        "timestamp":      [base + pd.Timedelta(minutes=6 * i) for i in range(20)],
    })


@pytest.fixture
def merchant_df() -> pd.DataFrame:
    """60 unique senders → ACC_MERCHANT, no outgoing from merchant."""
    senders = [f"ACC_C{i:02d}" for i in range(1, 61)]
    base = pd.Timestamp("2024-01-01 10:00:00")
    return pd.DataFrame({
        "transaction_id": [f"MC{i:03d}" for i in range(1, 61)],
        "sender_id":      senders,
        "receiver_id":    ["ACC_MERCHANT"] * 60,
        "amount":         [float(50 + i * 3) for i in range(60)],
        "timestamp":      [base + pd.Timedelta(minutes=5 * i) for i in range(60)],
    })


@pytest.fixture
def shell_chain_df() -> pd.DataFrame:
    """RICH1(5 txns) → SHELL1(3) → SHELL2(2) → RICH2(4 txns). Valid 3-hop chain."""
    return pd.DataFrame({
        "transaction_id": [f"SC{i:03d}" for i in range(1, 11)],
        "sender_id": [
            "ACC_RICH1", "ACC_RICH1",
            "ACC_SHELL1",
            "ACC_SHELL2",
            "ACC_RICH1", "ACC_RICH1", "ACC_RICH1",
            "ACC_OTHER4", "ACC_OTHER5", "ACC_OTHER6",
        ],
        "receiver_id": [
            "ACC_SHELL1", "ACC_SHELL1",
            "ACC_SHELL2",
            "ACC_RICH2",
            "ACC_OTHER1", "ACC_OTHER2", "ACC_OTHER3",
            "ACC_RICH2", "ACC_RICH2", "ACC_RICH2",
        ],
        "amount": [9500.0, 8500.0, 17500.0, 17000.0,
                   5000.0, 3000.0, 2000.0,
                   4000.0, 6000.0, 5500.0],
        "timestamp": pd.to_datetime([
            "2024-01-01 09:00:00", "2024-01-01 09:30:00",
            "2024-01-01 10:00:00",
            "2024-01-01 11:00:00",
            "2024-01-01 12:00:00", "2024-01-01 13:00:00", "2024-01-01 14:00:00",
            "2024-01-02 09:00:00", "2024-01-02 10:00:00", "2024-01-02 11:00:00",
        ]),
    })


# ── Graphs ────────────────────────────────────────────────────────────────────

@pytest.fixture
def triangle_graph(triangle_df):
    return build_graph(triangle_df)


@pytest.fixture
def fan_in_graph(fan_in_df):
    return build_graph(fan_in_df)


@pytest.fixture
def fan_out_graph(fan_out_df):
    return build_graph(fan_out_df)


@pytest.fixture
def shell_chain_graph(shell_chain_df):
    return build_graph(shell_chain_df)


# ── Raw fixture bytes (for endpoint tests) ────────────────────────────────────

@pytest.fixture
def triangle_csv_bytes() -> bytes:
    return (FIXTURES_DIR / "triangle_cycle.csv").read_bytes()


@pytest.fixture
def fan_in_csv_bytes() -> bytes:
    return (FIXTURES_DIR / "fan_in_smurfing.csv").read_bytes()


@pytest.fixture
def mixed_csv_bytes() -> bytes:
    return (FIXTURES_DIR / "mixed_patterns.csv").read_bytes()
