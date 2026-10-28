"""Tests the real box-score-informed APM dataset builder and Ridge
fit: a team's real point differential must be attributed correctly,
a thin-sample player must fold into the "OTHER" column, and a player
whose real presence consistently coincides with real team wins should
get a positive real coefficient."""
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.nba_apm_model import build_apm_dataset, fit_apm_ratings  # noqa: E402


def _historical(rows):
    return pd.DataFrame(rows, columns=["match_id", "home_team", "away_team", "home_score", "away_score"])


def _plus_minus(rows):
    return pd.DataFrame(rows, columns=["match_id", "team", "player_name", "minutes", "plus_minus"])


def test_team_point_diff_is_signed_correctly_for_home_and_away():
    hist = _historical([("G1", "A", "B", 110, 100)])
    pm = _plus_minus([
        ("G1", "A", "STAR_A", "48", 10),
        ("G1", "B", "STAR_B", "48", -10),
    ])
    X, y = build_apm_dataset(pm, hist)
    assert y.iloc[0] == 10  # team A's row: +10
    assert y.iloc[1] == -10  # team B's row: -10


def test_thin_sample_player_folds_into_other_column():
    hist = _historical([(f"G{i}", "A", "B", 100, 90) for i in range(12)])
    rows = []
    for i in range(12):
        rows.append((f"G{i}", "A", "REGULAR", "40", 10))
        rows.append((f"G{i}", "B", "OPP", "40", -10))
        if i < 3:  # fewer than MIN_REAL_GAMES (10) real appearances
            rows.append((f"G{i}", "A", "ONE_OFF", "5", 1))
    pm = _plus_minus(rows)
    X, _ = build_apm_dataset(pm, hist)
    assert "REGULAR" in X.columns
    assert "ONE_OFF" not in X.columns  # fewer than MIN_REAL_GAMES appearances
    assert "OTHER" in X.columns


def test_player_present_in_wins_gets_positive_coefficient():
    rows_hist, rows_pm = [], []
    for i in range(20):
        rows_hist.append((f"G{i}", "A", "B", 120, 90))  # team A always wins by 30
        rows_pm.append((f"G{i}", "A", "IMPACT_PLAYER", "48", 15))
        rows_pm.append((f"G{i}", "B", "OPPONENT", "48", -15))
    hist = _historical(rows_hist)
    pm = _plus_minus(rows_pm)
    X, y = build_apm_dataset(pm, hist)
    ratings = fit_apm_ratings(X, y)
    assert ratings["IMPACT_PLAYER"] > 0
