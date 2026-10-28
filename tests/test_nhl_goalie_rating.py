"""Tests the real per-team goalie GSAx signal: a goalie who outperforms
expected goals (real GSAx > 0) should rate above a league-average
goalie, shrinkage must pull a thin-sample goalie toward zero, and the
"most-used" tiebreak must pick the real highest-games-played goalie
per team, never an arbitrary one."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.nhl_goalie_rating import team_primary_goalie_gsax  # noqa: E402


def _goalies(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["team", "name", "games_played", "xGoals", "goals"])


def test_outperforming_goalie_has_positive_gsax():
    df = _goalies([("BOS", "GOALIE_A", 40, 100.0, 80.0)])  # allowed 20 fewer real goals than expected
    ratings = team_primary_goalie_gsax(df)
    gsax, games = ratings["BOS"]
    assert gsax > 0
    assert games == 40


def test_underperforming_goalie_has_negative_gsax():
    df = _goalies([("BOS", "GOALIE_A", 40, 80.0, 100.0)])  # allowed 20 MORE real goals than expected
    ratings = team_primary_goalie_gsax(df)
    gsax, _ = ratings["BOS"]
    assert gsax < 0


def test_most_used_goalie_is_picked_per_team():
    df = _goalies([
        ("BOS", "BACKUP", 10, 20.0, 19.0),
        ("BOS", "STARTER", 50, 120.0, 110.0),
    ])
    ratings = team_primary_goalie_gsax(df)
    _, games = ratings["BOS"]
    assert games == 50  # the real starter (more games), not the backup


def test_thin_sample_goalie_is_shrunk_toward_zero():
    thin = _goalies([("BOS", "ROOKIE", 2, 6.0, 2.0)])  # a real, large per-game GSAx on a tiny sample
    thick = _goalies([("BOS", "VETERAN", 60, 150.0, 100.0)])  # a smaller real per-game GSAx on a full season
    thin_gsax, _ = team_primary_goalie_gsax(thin)["BOS"]
    thick_gsax, _ = team_primary_goalie_gsax(thick)["BOS"]
    raw_thin_per_game = (6.0 - 2.0) / 2  # 2.0
    raw_thick_per_game = (150.0 - 100.0) / 60  # 0.833
    assert thin_gsax < raw_thin_per_game  # pulled well below its own real raw rate
    # Real shrinkage formula: raw * games / (games + SHRINK_K) -- at 60
    # games and SHRINK_K=15, that's exactly 0.8x, not "barely shrunk" in
    # absolute terms, but proportionally far less shrunk than the
    # 2-game rookie above (2/(2+15) = 0.12x).
    assert thick_gsax == pytest.approx(raw_thick_per_game * 60 / 75, abs=1e-6)
    assert (thick_gsax / raw_thick_per_game) > (thin_gsax / raw_thin_per_game)
