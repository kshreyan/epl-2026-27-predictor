"""Tests the real per-QB Elo-style rating: a QB whose team wins big
should gain rating, shrinkage must pull thin-sample QBs toward the
league baseline, and a missing real starter must never be guessed."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.nfl_qb_rating import (  # noqa: E402
    BASELINE_RATING,
    fit_qb_elo,
    qb_adjustment,
    shrink_qb_ratings,
)


def _games(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["date", "home_qb_name", "away_qb_name", "home_score", "away_score"])


def test_winning_qb_gains_rating_and_losing_qb_loses_it():
    games = _games([
        ("2026-09-01", "QB_A", "QB_B", 30, 10),
        ("2026-09-08", "QB_A", "QB_B", 28, 14),
    ])
    ratings, _ = fit_qb_elo(games)
    assert ratings["QB_A"] > BASELINE_RATING
    assert ratings["QB_B"] < BASELINE_RATING


def test_new_qb_starts_at_baseline_before_any_games():
    games = _games([("2026-09-01", "QB_A", "QB_B", 20, 20)])
    ratings, n_starts = fit_qb_elo(games)
    # An exact tie leaves both ratings at baseline (expected_score ==
    # 0.5 == actual_score for an even pre-game rating).
    assert ratings["QB_A"] == pytest.approx(BASELINE_RATING)
    assert n_starts["QB_A"] == 1


def test_games_missing_a_real_qb_name_are_skipped_not_guessed():
    games = pd.DataFrame([
        {"date": "2026-09-01", "home_qb_name": "QB_A", "away_qb_name": None, "home_score": 30, "away_score": 10},
        {"date": "2026-09-08", "home_qb_name": "QB_A", "away_qb_name": "QB_B", "home_score": 20, "away_score": 17},
    ])
    ratings, n_starts = fit_qb_elo(games)
    assert n_starts["QB_A"] == 1  # only the second, real-both-QBs game counted
    assert "QB_B" in ratings


def test_shrinkage_pulls_a_thin_sample_qb_toward_baseline():
    raw_ratings = {"VETERAN": 1700.0, "ROOKIE": 1700.0}
    n_starts = {"VETERAN": 100, "ROOKIE": 1}
    shrunk = shrink_qb_ratings(raw_ratings, n_starts, shrink_k=8.0)
    assert shrunk["VETERAN"] > shrunk["ROOKIE"]
    assert shrunk["ROOKIE"] < raw_ratings["ROOKIE"]
    # 100 real starts should leave the veteran's rating barely shrunk.
    assert shrunk["VETERAN"] == pytest.approx(1700.0, abs=15.0)


def test_qb_adjustment_is_signed_difference_favoring_home():
    shrunk = {"HOME_QB": 1600.0, "AWAY_QB": 1500.0}
    assert qb_adjustment("HOME_QB", "AWAY_QB", shrunk) == pytest.approx(100.0)


def test_qb_adjustment_is_none_when_a_real_starter_is_unknown():
    assert qb_adjustment(None, "AWAY_QB", {"AWAY_QB": 1500.0}) is None
    assert qb_adjustment("HOME_QB", None, {"HOME_QB": 1500.0}) is None
