"""Tests real rest-day computation: each team's rest is real days since
its own last real game, and a team's season-opening game has no real
value to report (never a guessed default)."""
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.nba_rest_features import compute_rest_days  # noqa: E402


def _games(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["date", "home_team", "away_team"])


def test_season_opener_has_no_real_rest_value():
    df = compute_rest_days(_games([("2026-10-01", "A", "B")]))
    assert pd.isna(df.loc[0, "home_rest_days"])
    assert pd.isna(df.loc[0, "away_rest_days"])


def test_back_to_back_is_one_real_rest_day():
    # Same convention nflverse's own real home_rest/away_rest columns
    # use (already adopted for NFL in Phase 1): rest_days is the raw
    # real calendar-day gap between games, not "days completely off"
    # (gap - 1) -- a real back-to-back (games on consecutive real
    # calendar days) is rest_days == 1, the smallest real gap possible.
    df = compute_rest_days(_games([
        ("2026-10-01", "A", "B"),
        ("2026-10-02", "A", "C"),  # A plays again the very next day
    ]))
    assert df.loc[1, "home_rest_days"] == 1


def test_rest_counts_real_calendar_days_since_last_game():
    df = compute_rest_days(_games([
        ("2026-10-01", "A", "B"),
        ("2026-10-05", "A", "C"),  # A's next game, 4 real days later
    ]))
    assert df.loc[1, "home_rest_days"] == 4


def test_a_team_can_be_home_in_one_game_and_away_in_the_next():
    df = compute_rest_days(_games([
        ("2026-10-01", "A", "B"),
        ("2026-10-03", "C", "A"),  # A is away this time
    ]))
    assert df.loc[1, "away_rest_days"] == 2
