"""Unit tests for app/engine/scoring.py."""

import networkx as nx
import pytest

from app.engine.scoring import compute_scores, _score_patterns


# ── _score_patterns (pure function) ──────────────────────────────────────────

def test_cycle_length_3_score():
    assert _score_patterns(["cycle_length_3"]) == 40.0


def test_cycle_length_4_score():
    assert _score_patterns(["cycle_length_4"]) == 32.0


def test_cycle_length_5_score():
    assert _score_patterns(["cycle_length_5"]) == 25.0


def test_smurfing_fan_in_score():
    assert _score_patterns(["smurfing_fan_in"]) == 25.0


def test_smurfing_fan_out_score():
    assert _score_patterns(["smurfing_fan_out"]) == 22.0


def test_shell_intermediary_score():
    assert _score_patterns(["shell_intermediary"]) == 20.0


def test_shell_source_score():
    assert _score_patterns(["shell_source"]) == 15.0


def test_empty_patterns_score_zero():
    assert _score_patterns([]) == 0.0


def test_unknown_pattern_scores_zero():
    assert _score_patterns(["nonexistent_pattern"]) == 0.0


# ── Cross-category scoring (additive) ────────────────────────────────────────

def test_cycle_plus_smurfing():
    assert _score_patterns(["cycle_length_3", "smurfing_fan_in"]) == 65.0


def test_cycle_plus_shell():
    assert _score_patterns(["cycle_length_3", "shell_intermediary"]) == 60.0


def test_smurfing_plus_shell():
    assert _score_patterns(["smurfing_fan_in", "shell_intermediary"]) == 45.0


def test_all_three_categories():
    assert _score_patterns(["cycle_length_3", "smurfing_fan_in", "shell_intermediary"]) == 85.0


# ── Within-category max (not additive) ───────────────────────────────────────

def test_within_cycle_takes_max():
    # cycle_length_3=40 > cycle_length_4=32 → result is 40, not 72
    assert _score_patterns(["cycle_length_3", "cycle_length_4"]) == 40.0


def test_within_smurfing_takes_max():
    # fan_in=25 > fan_out=22 → result is 25, not 47
    assert _score_patterns(["smurfing_fan_in", "smurfing_fan_out"]) == 25.0


def test_within_shell_takes_max():
    # intermediary=20 > source=15 → result is 20, not 35
    assert _score_patterns(["shell_intermediary", "shell_source"]) == 20.0


# ── compute_scores (with suppression) ────────────────────────────────────────

def test_suppressed_flag_excluded_from_score(settings):
    G = nx.DiGraph()
    combined = {"ACC_A": ["smurfing_fan_out", "cycle_length_3"]}
    suppressed = {"ACC_A": ["smurfing_fan_out"]}
    scores = compute_scores(combined, suppressed, G, settings)
    # Only cycle_length_3 (40) should count
    assert scores["ACC_A"] == 40.0


def test_all_flags_suppressed_scores_zero(settings):
    G = nx.DiGraph()
    combined = {"ACC_A": ["smurfing_fan_out"]}
    suppressed = {"ACC_A": ["smurfing_fan_out"]}
    scores = compute_scores(combined, suppressed, G, settings)
    assert scores["ACC_A"] == 0.0


def test_no_suppression_full_score(settings):
    G = nx.DiGraph()
    combined = {"ACC_A": ["cycle_length_3", "smurfing_fan_in"]}
    scores = compute_scores(combined, {}, G, settings)
    assert scores["ACC_A"] == 65.0
