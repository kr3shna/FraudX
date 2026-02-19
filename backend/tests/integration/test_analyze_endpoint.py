"""Integration tests for POST /api/analyze."""

import pathlib

import pytest

FIXTURES = pathlib.Path("tests/fixtures")


# ── Happy path ────────────────────────────────────────────────────────────────

def test_analyze_triangle_returns_200(client, triangle_csv_bytes):
    r = client.post("/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")})
    assert r.status_code == 200


def test_analyze_response_has_required_fields(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    assert "status" in body
    assert "session_token" in body
    assert "validation_summary" in body
    assert "result" in body
    assert "suspicious_accounts" in body["result"]
    assert "fraud_rings" in body["result"]
    assert "summary" in body["result"]


def test_analyze_status_is_success(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    assert body["status"] == "success"


def test_analyze_session_token_non_empty(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    assert len(body["session_token"]) > 0


def test_analyze_triangle_three_suspicious_accounts(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    assert len(body["result"]["suspicious_accounts"]) == 3


def test_analyze_triangle_one_ring(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    assert len(body["result"]["fraud_rings"]) == 1
    assert body["result"]["fraud_rings"][0]["ring_id"] == "RING_001"


def test_analyze_validation_summary_counts(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    vs = body["validation_summary"]
    assert vs["rows_total"] == 3
    assert vs["rows_accepted"] == 3
    assert vs["rows_skipped"] == 0


# ── Ordering guarantees ───────────────────────────────────────────────────────

def test_suspicious_accounts_sorted_score_desc(client, mixed_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("m.csv", mixed_csv_bytes, "text/csv")}
    ).json()
    scores = [a["suspicion_score"] for a in body["result"]["suspicious_accounts"]]
    assert scores == sorted(scores, reverse=True)


def test_member_accounts_sorted_alphabetically(client, triangle_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    ).json()
    members = body["result"]["fraud_rings"][0]["member_accounts"]
    assert members == sorted(members)


def test_detected_patterns_sorted_alphabetically(client, mixed_csv_bytes):
    body = client.post(
        "/api/analyze", files={"file": ("m.csv", mixed_csv_bytes, "text/csv")}
    ).json()
    for account in body["result"]["suspicious_accounts"]:
        patterns = account["detected_patterns"]
        assert patterns == sorted(patterns)


# ── Mixed patterns score ──────────────────────────────────────────────────────

def test_mixed_patterns_acc_a_higher_score(client, mixed_csv_bytes):
    """ACC_A has both cycle + smurfing, so it scores higher than ACC_B/C (cycle only)."""
    body = client.post(
        "/api/analyze", files={"file": ("m.csv", mixed_csv_bytes, "text/csv")}
    ).json()
    accounts = {a["account_id"]: a for a in body["result"]["suspicious_accounts"]}
    assert "ACC_A" in accounts
    assert "cycle_length_3" in accounts["ACC_A"]["detected_patterns"]
    assert "smurfing_fan_in" in accounts["ACC_A"]["detected_patterns"]
    # Multi-pattern account must outscore single-pattern accounts
    assert accounts["ACC_A"]["suspicion_score"] > accounts["ACC_B"]["suspicion_score"]


# ── Suppression ───────────────────────────────────────────────────────────────

def test_payroll_sender_not_in_suspicious_accounts(client):
    csv_bytes = (FIXTURES / "payroll_pattern.csv").read_bytes()
    body = client.post(
        "/api/analyze", files={"file": ("p.csv", csv_bytes, "text/csv")}
    ).json()
    account_ids = [a["account_id"] for a in body["result"]["suspicious_accounts"]]
    assert "ACC_EMPLOYER" not in account_ids


def test_merchant_not_in_suspicious_accounts(client):
    csv_bytes = (FIXTURES / "merchant_pattern.csv").read_bytes()
    body = client.post(
        "/api/analyze", files={"file": ("m.csv", csv_bytes, "text/csv")}
    ).json()
    account_ids = [a["account_id"] for a in body["result"]["suspicious_accounts"]]
    assert "ACC_MERCHANT" not in account_ids


# ── Error responses ───────────────────────────────────────────────────────────

def test_non_csv_returns_415(client):
    r = client.post(
        "/api/analyze", files={"file": ("data.txt", b"hello", "text/plain")}
    )
    assert r.status_code == 415


def test_missing_required_column_returns_400(client):
    bad_csv = b"transaction_id,sender_id,amount\nT1,ACC_A,100\n"
    r = client.post(
        "/api/analyze", files={"file": ("bad.csv", bad_csv, "text/csv")}
    )
    assert r.status_code == 400
    assert "Missing required columns" in r.json()["detail"]


def test_empty_csv_returns_400(client):
    csv = b"transaction_id,sender_id,receiver_id,amount,timestamp\n"
    r = client.post(
        "/api/analyze", files={"file": ("empty.csv", csv, "text/csv")}
    )
    assert r.status_code == 400


def test_all_invalid_rows_returns_400(client):
    csv = (
        b"transaction_id,sender_id,receiver_id,amount,timestamp\n"
        b"T1,ACC_A,ACC_A,100.00,2024-01-01 10:00:00\n"   # self-loop
    )
    r = client.post(
        "/api/analyze", files={"file": ("bad.csv", csv, "text/csv")}
    )
    assert r.status_code == 400
