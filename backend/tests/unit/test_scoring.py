"""Unit tests for app/engine/scoring.py (continuous scoring engine)."""

import pytest
from app.engine.scoring import compute_scores
from app.models.algorithm_result import AlgorithmResult


# ── compute_scores: basic combination ────────────────────────────────────────

def test_cycle_only_score():
    scores = compute_scores(
        cycle_scores={"ACC_A": 38.0},
        smurfing_scores={},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 38.0


def test_smurfing_only_score():
    scores = compute_scores(
        cycle_scores={},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 20.0


def test_shell_only_score():
    scores = compute_scores(
        cycle_scores={},
        smurfing_scores={},
        shell_scores={"ACC_A": 14.0},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 14.0


def test_all_three_categories_sum():
    scores = compute_scores(
        cycle_scores={"ACC_A": 38.0},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={"ACC_A": 14.0},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 72.0


def test_scores_across_different_accounts():
    scores = compute_scores(
        cycle_scores={"ACC_A": 38.0},
        smurfing_scores={"ACC_B": 18.0},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 38.0
    assert scores["ACC_B"] == 18.0


# ── Suppression multiplier applied to smurfing only ──────────────────────────

def test_full_suppression_multiplier():
    """Multiplier 0.1 reduces smurfing score by 90%, cycle untouched."""
    scores = compute_scores(
        cycle_scores={"ACC_A": 38.0},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={},
        suppression_multipliers={"ACC_A": 0.1},
    )
    expected = round(38.0 + 20.0 * 0.1, 1)
    assert scores["ACC_A"] == expected


def test_half_suppression_multiplier():
    scores = compute_scores(
        cycle_scores={},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={},
        suppression_multipliers={"ACC_A": 0.5},
    )
    assert scores["ACC_A"] == 10.0


def test_no_multiplier_defaults_to_one():
    """Account with no entry in suppression_multipliers uses multiplier 1.0."""
    scores = compute_scores(
        cycle_scores={},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 20.0


def test_multiplier_does_not_affect_cycle_or_shell():
    """Suppression only scales smurfing — cycle and shell are unaffected."""
    scores = compute_scores(
        cycle_scores={"ACC_A": 38.0},
        smurfing_scores={"ACC_A": 20.0},
        shell_scores={"ACC_A": 14.0},
        suppression_multipliers={"ACC_A": 0.0},
    )
    assert scores["ACC_A"] == round(38.0 + 0.0 + 14.0, 1)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_inputs_returns_empty():
    assert compute_scores({}, {}, {}, {}) == {}


def test_zero_scores_not_included_when_all_zero():
    scores = compute_scores(
        cycle_scores={"ACC_A": 0.0},
        smurfing_scores={},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == 0.0


def test_score_rounds_to_one_decimal():
    scores = compute_scores(
        cycle_scores={"ACC_A": 10.123},
        smurfing_scores={"ACC_A": 5.456},
        shell_scores={},
        suppression_multipliers={},
    )
    assert scores["ACC_A"] == round(10.123 + 5.456, 1)
