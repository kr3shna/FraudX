"""Unit tests for app/engine/ring_merger.py."""

import pytest

from app.engine.ring_merger import merge_rings, _classify_pattern_type, _compute_ring_risk


# ── _classify_pattern_type ────────────────────────────────────────────────────

def test_classify_cycle_only():
    assert _classify_pattern_type({"cycle_length_3"}) == "cycle"


def test_classify_smurfing_only():
    assert _classify_pattern_type({"smurfing_fan_in"}) == "smurfing"


def test_classify_shell_only():
    assert _classify_pattern_type({"shell_intermediary"}) == "shell"


def test_classify_mixed_cycle_and_smurfing():
    assert _classify_pattern_type({"cycle_length_3", "smurfing_fan_in"}) == "mixed"


def test_classify_empty_patterns():
    assert _classify_pattern_type(set()) == "unknown"


# ── _compute_ring_risk ────────────────────────────────────────────────────────

def test_ring_risk_cycle3_bonus():
    group = {"ACC_A", "ACC_B", "ACC_C"}
    scores = {"ACC_A": 40.0, "ACC_B": 40.0, "ACC_C": 40.0}
    patterns = {"cycle_length_3"}
    # base=40, pattern_bonus=0 (1 type → (1-1)*5=0), cycle3_bonus=10 → 50
    risk = _compute_ring_risk(group, scores, patterns)
    assert risk == 50.0


def test_ring_risk_mixed_bonus():
    group = {"ACC_A", "ACC_B"}
    scores = {"ACC_A": 65.0, "ACC_B": 40.0}
    patterns = {"cycle_length_3", "smurfing_fan_in"}
    # base=(65+40)/2=52.5, pattern_bonus=min(15,(2-1)*5)=5, cycle3=10 → 67.5
    risk = _compute_ring_risk(group, scores, patterns)
    assert risk == 67.5


def test_ring_risk_capped_at_100():
    group = {"A", "B", "C"}
    scores = {"A": 85.0, "B": 85.0, "C": 85.0}
    patterns = {"cycle_length_3", "smurfing_fan_in", "shell_intermediary"}
    risk = _compute_ring_risk(group, scores, patterns)
    assert risk <= 100.0


# ── merge_rings ───────────────────────────────────────────────────────────────

def test_triangle_forms_ring(settings):
    cluster = [{"ACC_A", "ACC_B", "ACC_C"}]
    scores = {"ACC_A": 40.0, "ACC_B": 40.0, "ACC_C": 40.0}
    flags = {acc: ["cycle_length_3"] for acc in ["ACC_A", "ACC_B", "ACC_C"]}

    rings = merge_rings(cluster, scores, flags, {}, settings)

    assert len(rings) == 1
    assert rings[0].ring_id == "RING_001"
    assert sorted(rings[0].member_accounts) == ["ACC_A", "ACC_B", "ACC_C"]
    assert rings[0].pattern_type == "cycle"


def test_singleton_below_threshold_not_in_rings(settings):
    scores = {"ACC_A": 25.0}  # below threshold 40
    flags = {"ACC_A": ["smurfing_fan_in"]}
    rings = merge_rings([], scores, flags, {}, settings)
    assert rings == []


def test_singleton_above_threshold_not_in_rings(settings):
    """Account above threshold but in no cluster → ring_id NONE, not in fraud_rings list."""
    scores = {"ACC_A": 40.0}
    flags = {"ACC_A": ["cycle_length_3"]}
    # No clusters → ACC_A forms a singleton group → not in rings list
    rings = merge_rings([], scores, flags, {}, settings)
    assert rings == []


def test_two_separate_cycles_form_two_rings(settings):
    cluster1 = {"ACC_A", "ACC_B", "ACC_C"}
    cluster2 = {"ACC_X", "ACC_Y", "ACC_Z"}
    scores = {acc: 40.0 for acc in list(cluster1) + list(cluster2)}
    flags = {acc: ["cycle_length_3"] for acc in scores}

    rings = merge_rings([cluster1, cluster2], scores, flags, {}, settings)
    assert len(rings) == 2
    ring_ids = {r.ring_id for r in rings}
    assert "RING_001" in ring_ids
    assert "RING_002" in ring_ids


def test_overlapping_clusters_merge_into_one_ring(settings):
    """If two clusters share a member, they should merge into one ring."""
    cluster1 = {"ACC_A", "ACC_B", "ACC_C"}
    cluster2 = {"ACC_C", "ACC_D", "ACC_E"}   # ACC_C is shared
    scores = {acc: 40.0 for acc in ["ACC_A", "ACC_B", "ACC_C", "ACC_D", "ACC_E"]}
    flags = {acc: ["cycle_length_3"] for acc in scores}

    rings = merge_rings([cluster1, cluster2], scores, flags, {}, settings)
    assert len(rings) == 1
    assert len(rings[0].member_accounts) == 5


def test_rings_sorted_by_risk_score_desc(settings):
    """Larger ring (higher base score) should come first."""
    cluster_big = {"ACC_A", "ACC_B", "ACC_C"}
    cluster_small = {"ACC_X", "ACC_Y", "ACC_Z"}
    scores = {
        "ACC_A": 65.0, "ACC_B": 65.0, "ACC_C": 65.0,
        "ACC_X": 40.0, "ACC_Y": 40.0, "ACC_Z": 40.0,
    }
    flags = {
        **{acc: ["cycle_length_3", "smurfing_fan_in"] for acc in cluster_big},
        **{acc: ["cycle_length_3"] for acc in cluster_small},
    }

    rings = merge_rings([cluster_big, cluster_small], scores, flags, {}, settings)
    assert rings[0].risk_score >= rings[1].risk_score


def test_member_accounts_sorted_alphabetically(settings):
    cluster = {"ACC_C", "ACC_A", "ACC_B"}
    scores = {"ACC_A": 40.0, "ACC_B": 40.0, "ACC_C": 40.0}
    flags = {acc: ["cycle_length_3"] for acc in scores}

    rings = merge_rings([cluster], scores, flags, {}, settings)
    assert rings[0].member_accounts == ["ACC_A", "ACC_B", "ACC_C"]
