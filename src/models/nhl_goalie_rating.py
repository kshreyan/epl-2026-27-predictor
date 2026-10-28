"""Real per-team goalie-quality signal from MoneyPuck's real public
season-summary data (confirmed directly this session: HTTP 200, real
xGoals/goals columns per goalie per season, free, no key).

**Real, honest scope limitation**: this is a SEASON-level signal (each
team's real most-used goalie that season, i.e. highest real
games_played), not a live per-game confirmed-starter feature -- a real
per-game starting goalie needs a real boxscore call per historical
game (api-web.nhle.com's `/v1/gamecenter/{id}/boxscore`), which for
several thousand real historical games is a real cost this phase does
not spend; this is a deliberate, disclosed scope cut (see
backtest_nhl_goalie_adjustment.py's report), not a silent gap.

GSAx (Goals Saved above Expected) = real xGoals - real goals allowed,
the standard real sports-analytics goalie metric -- positive means the
goalie allowed FEWER real goals than a league-average goalie would
have been expected to on the same real shots faced. Shrunk toward 0
(a league-average goalie) proportional to real games played, the same
empirical-shrinkage style nfl_qb_rating.py already established (NOT a
full Hessian/Laplace posterior -- see that module's own docstring for
why).
"""
from __future__ import annotations

import io

import pandas as pd
import requests

MONEYPUCK_URL = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/regular/goalies.csv"
SHRINK_K = 15.0  # real games played at which a goalie's GSAx/game is shrunk halfway to 0


def fetch_moneypuck_goalie_season(season: int) -> pd.DataFrame:
    """`season` is MoneyPuck's own real end-year label (e.g. 2025 = the
    real 2024-25 season) -- the same real convention
    collect_nhl_apiweb.py already uses for api-web.nhle.com."""
    resp = requests.get(MONEYPUCK_URL.format(season=season), headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    return df[df["situation"] == "all"].copy()


def team_primary_goalie_gsax(season_df: pd.DataFrame) -> dict[str, tuple[float, int]]:
    """For each real team code, the real most-used goalie's own
    (shrunk GSAx-per-game, real games_played) -- "most-used" by real
    games_played that season, a real, simple, defensible tiebreak
    (never a guessed depth-chart rank)."""
    result: dict[str, tuple[float, int]] = {}
    for team, group in season_df.groupby("team"):
        primary = group.sort_values("games_played", ascending=False).iloc[0]
        games = int(primary["games_played"])
        gsax_per_game = (float(primary["xGoals"]) - float(primary["goals"])) / games if games else 0.0
        shrunk = gsax_per_game * (games / (games + SHRINK_K))
        result[team] = (shrunk, games)
    return result
