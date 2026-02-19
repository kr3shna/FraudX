"""Integration tests for GET /api/results."""

import pytest


def _post_triangle(client, triangle_csv_bytes) -> str:
    """Upload triangle CSV and return the session token."""
    r = client.post(
        "/api/analyze",
        files={"file": ("t.csv", triangle_csv_bytes, "text/csv")},
    )
    assert r.status_code == 200
    return r.json()["session_token"]


def _post_mixed(client, mixed_csv_bytes) -> str:
    r = client.post(
        "/api/analyze",
        files={"file": ("m.csv", mixed_csv_bytes, "text/csv")},
    )
    assert r.status_code == 200
    return r.json()["session_token"]


# ── Basic retrieval ───────────────────────────────────────────────────────────

def test_get_results_returns_200(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get("/api/results", headers={"X-Session-Token": token})
    assert r.status_code == 200


def test_get_results_contains_correct_fields(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    body = client.get("/api/results", headers={"X-Session-Token": token}).json()
    assert "suspicious_accounts" in body
    assert "fraud_rings" in body
    assert "summary" in body


def test_get_results_returns_same_data_as_analyze(client, triangle_csv_bytes):
    r = client.post(
        "/api/analyze", files={"file": ("t.csv", triangle_csv_bytes, "text/csv")}
    )
    token = r.json()["session_token"]
    analyze_result = r.json()["result"]

    get_result = client.get(
        "/api/results", headers={"X-Session-Token": token}
    ).json()

    assert get_result["suspicious_accounts"] == analyze_result["suspicious_accounts"]
    assert get_result["fraud_rings"] == analyze_result["fraud_rings"]


# ── Error cases ───────────────────────────────────────────────────────────────

def test_unknown_token_returns_404(client):
    r = client.get("/api/results", headers={"X-Session-Token": "doesnotexist"})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_missing_header_returns_422(client):
    r = client.get("/api/results")
    assert r.status_code == 422


# ── min_score filter ──────────────────────────────────────────────────────────

def test_min_score_filters_below_threshold(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    # All triangle accounts score 40.0; min_score=50 should exclude them all
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"min_score": 50},
    )
    assert r.status_code == 200
    assert r.json()["suspicious_accounts"] == []


def test_min_score_keeps_accounts_at_threshold(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    # All three cycle accounts score ~28; min_score=25 includes them all
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"min_score": 25},
    )
    assert len(r.json()["suspicious_accounts"]) == 3


def test_min_score_filters_mixed_patterns(client, mixed_csv_bytes):
    token = _post_mixed(client, mixed_csv_bytes)
    # ACC_A (cycle + smurfing) scores higher than ACC_B/C (cycle only)
    # min_score=35 should include ACC_A but not necessarily all cycle-only accounts
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"min_score": 35},
    )
    accounts = r.json()["suspicious_accounts"]
    account_ids = [a["account_id"] for a in accounts]
    assert "ACC_A" in account_ids


# ── account_id filter ─────────────────────────────────────────────────────────

def test_account_id_filter(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"account_id": "ACC_A"},
    )
    accounts = r.json()["suspicious_accounts"]
    assert len(accounts) == 1
    assert accounts[0]["account_id"] == "ACC_A"


def test_account_id_filter_no_match(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"account_id": "ACC_NOBODY"},
    )
    assert r.json()["suspicious_accounts"] == []


# ── ring_id filter ────────────────────────────────────────────────────────────

def test_ring_id_filter(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"ring_id": "RING_001"},
    )
    body = r.json()
    # All 3 accounts belong to RING_001
    assert len(body["suspicious_accounts"]) == 3
    assert len(body["fraud_rings"]) == 1
    assert body["fraud_rings"][0]["ring_id"] == "RING_001"


def test_ring_id_filter_no_match(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"ring_id": "RING_999"},
    )
    assert r.json()["suspicious_accounts"] == []
    assert r.json()["fraud_rings"] == []


# ── pattern filter ────────────────────────────────────────────────────────────

def test_pattern_filter_cycle(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"pattern": "cycle_length_3"},
    )
    assert len(r.json()["suspicious_accounts"]) == 3


def test_pattern_filter_no_match(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    r = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"pattern": "smurfing_fan_in"},
    )
    assert r.json()["suspicious_accounts"] == []


# ── Summary unchanged by filters ──────────────────────────────────────────────

def test_summary_unchanged_by_min_score_filter(client, triangle_csv_bytes):
    token = _post_triangle(client, triangle_csv_bytes)
    full = client.get("/api/results", headers={"X-Session-Token": token}).json()
    filtered = client.get(
        "/api/results",
        headers={"X-Session-Token": token},
        params={"min_score": 99},
    ).json()
    # Summary always reflects the original full analysis
    assert filtered["summary"] == full["summary"]
