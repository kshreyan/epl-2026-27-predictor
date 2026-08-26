"""Unit tests for the BTTS/totals/Asian-Handicap derivations in
scoreline_models.py -- pure math over a synthetic scoreline matrix, no
real data files needed, so these run in the fast suite. Added
alongside the spread/BTTS/totals prediction feature (previously only
manually sanity-checked, per the same discipline every other derived
number in this project has unit tests for).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.scoreline_models import (  # noqa: E402
    asian_handicap_home_cover_probability,
    btts_probability,
    model_fair_handicap_line,
    outcome_probabilities,
    score_matrix,
    total_goals_probabilities,
)


def test_btts_probability_matches_manual_sum():
    matrix = score_matrix(lam=1.4, mu=1.1, rho=-0.1)
    expected = sum(matrix[i, j] for i in range(1, matrix.shape[0]) for j in range(1, matrix.shape[1]))
    assert btts_probability(matrix) == pytest.approx(expected)


def test_btts_probability_excludes_any_zero_scoreline():
    matrix = score_matrix(lam=1.4, mu=1.1, rho=-0.1)
    btts = btts_probability(matrix)
    zero_either_side = matrix[0, :].sum() + matrix[:, 0].sum() - matrix[0, 0]
    assert btts == pytest.approx(1.0 - zero_either_side)


def test_total_goals_probabilities_sum_to_one_and_match_outcome_probs():
    matrix = score_matrix(lam=1.6, mu=1.2, rho=-0.05)
    over, under = total_goals_probabilities(matrix, 2.5)
    assert over + under == pytest.approx(1.0)
    assert 0.0 <= over <= 1.0

    # A tiny total-goals line (below the minimum possible total, 0)
    # must give over_prob -> 1.
    over_min, under_min = total_goals_probabilities(matrix, -0.5)
    assert over_min == pytest.approx(1.0)
    assert under_min == pytest.approx(0.0)


def test_symmetric_match_has_zero_fair_handicap_line():
    # Equal lambda/mu (no home advantage baked in) -> the model should
    # see this as a genuine coin flip at a pick'em (0.0) line.
    matrix = score_matrix(lam=1.3, mu=1.3, rho=0.0)
    fair_line = model_fair_handicap_line(matrix)
    assert fair_line == pytest.approx(0.0)
    cover = asian_handicap_home_cover_probability(matrix, 0.0)
    assert cover == pytest.approx(0.5, abs=0.02)


def test_lopsided_match_favors_home_side_at_a_negative_handicap_line():
    matrix = score_matrix(lam=2.5, mu=0.6, rho=0.0)
    fair_line = model_fair_handicap_line(matrix)
    assert fair_line < 0  # the stronger (home) side must give goals to make it a coin flip
    cover = asian_handicap_home_cover_probability(matrix, fair_line)
    assert cover == pytest.approx(0.5, abs=0.03)

    # At a much smaller (less negative) line, the strong home side should
    # cover more often than at its own fair line.
    cover_easy_line = asian_handicap_home_cover_probability(matrix, 0.0)
    assert cover_easy_line > cover


def test_whole_number_line_push_is_treated_as_half_a_cover():
    matrix = score_matrix(lam=1.3, mu=1.3, rho=0.0)
    # P(home wins by exactly 1) contributes fully to a -1.0 cover, and a
    # push (home wins by exactly 1) at line -1.0 should count as half.
    cover_at_minus_1 = asian_handicap_home_cover_probability(matrix, -1.0)
    win_by_2_or_more = sum(
        matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i - j >= 2
    )
    win_by_exactly_1 = sum(
        matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i - j == 1
    )
    expected = win_by_2_or_more + 0.5 * win_by_exactly_1
    assert cover_at_minus_1 == pytest.approx(expected, abs=1e-6)


def test_quarter_line_is_average_of_two_adjacent_half_lines():
    matrix = score_matrix(lam=1.8, mu=1.0, rho=-0.08)
    quarter = asian_handicap_home_cover_probability(matrix, -0.75)
    half_below = asian_handicap_home_cover_probability(matrix, -0.5)
    half_above = asian_handicap_home_cover_probability(matrix, -1.0)
    assert quarter == pytest.approx((half_below + half_above) / 2, abs=1e-6)


def test_home_and_away_win_probs_from_outcome_probabilities_are_consistent_with_ah_at_pick_em():
    # At a 0.0 line, cover == a straight win, with a draw split 50/50
    # between the two sides (the push convention already exercised above).
    matrix = score_matrix(lam=1.5, mu=1.0, rho=-0.1)
    home_win, draw, away_win = outcome_probabilities(matrix)
    cover = asian_handicap_home_cover_probability(matrix, 0.0)
    assert cover == pytest.approx(home_win + 0.5 * draw, abs=1e-6)
