"""Real rest-days / back-to-back features for NBA, derived purely from
each team's own real game dates (no new data source needed -- every
NBA historical/fixture row already has a real date). A team's real
rest before a game is the raw real calendar-day gap since its own
previous real game -- the same convention nflverse's own real
home_rest/away_rest columns already use (adopted for NFL in Phase 1),
not "days completely off" (gap - 1). A real back-to-back (games on
consecutive real calendar days) is rest_days == 1, the smallest real
gap possible.

The real first game of a season for a team has no real prior game to
measure from -- `None` is returned for that row rather than a guessed
"well-rested" default.
"""
from __future__ import annotations

import pandas as pd


def compute_rest_days(games_df: pd.DataFrame) -> pd.DataFrame:
    """`games_df` must have real date/home_team/away_team columns (one
    row per real game). Returns a copy with two new real columns,
    `home_rest_days`/`away_rest_days` (int, or NaN for a team's real
    season-opening game)."""
    df = games_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    last_game_date: dict[str, pd.Timestamp] = {}
    home_rest, away_rest = [], []
    for _, row in df.iterrows():
        home, away, date = row["home_team"], row["away_team"], row["date"]
        home_rest.append((date - last_game_date[home]).days if home in last_game_date else None)
        away_rest.append((date - last_game_date[away]).days if away in last_game_date else None)
        last_game_date[home] = date
        last_game_date[away] = date

    df["home_rest_days"] = home_rest
    df["away_rest_days"] = away_rest
    return df
