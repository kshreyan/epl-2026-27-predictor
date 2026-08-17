"""In-house dynamic Elo rating engine, fit on real historical EPL results.

We tried the clubelo.com public API for external Elo priors but it was
unreachable (connection timeout) from this environment at collection
time (see config/data_sources.yaml). Rather than fabricate Elo numbers,
we compute Elo directly and transparently from
`data/raw/epl_historical_matches.csv` (2014/15-2025/26, real results
from football-data.co.uk). This is self-contained, reproducible, and
avoids an external dependency.

Method: standard World-Football-Elo-style update with a margin-of-
victory multiplier and home-advantage offset, run two passes:

  Pass 1 seeds every team's first-ever appearance at a flat 1500 to
  measure, empirically, where promoted teams' ratings actually settle
  by the end of their debut season relative to the league mean.

  Pass 2 re-runs the same history but seeds a team's first-ever
  appearance using that empirically observed promoted-team offset
  (see `compute_promoted_team_elo_offset`), which is a materially
  better starting prior for a newly promoted club than a flat 1500.

Between seasons, a returning team's rating is partially reverted
toward the (currently tracked) league-mean rating -- teams regress
over the close season (new signings, ageing squads, managerial
change) and Elo should not carry a full season's swings forward
undamped.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

INITIAL_RATING = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 60.0
SEASON_REVERSION = 1.0 / 3.0  # fraction reverted toward league mean at each new season


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_a - rating_b) / 400.0))


def _mov_multiplier(goal_diff: int, elo_diff_winner_perspective: float) -> float:
    """Margin-of-victory multiplier (World Football Elo Ratings formula)."""
    if goal_diff == 0:
        return 1.0
    return math.log(abs(goal_diff) + 1) * (2.2 / (abs(elo_diff_winner_perspective) * 0.001 + 2.2))


@dataclass
class EloRun:
    history: pd.DataFrame          # one row per match: pre/post ratings both teams
    final_ratings: dict[str, float]  # team -> rating after the last match in the input
    league_mean_by_date: pd.Series   # league-mean rating over time (for promoted-team offset calc)


def run_elo(
    matches: pd.DataFrame,
    seed_ratings: dict[str, float] | None = None,
    promoted_offset: float = 0.0,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    season_reversion: float = SEASON_REVERSION,
) -> EloRun:
    """Run the Elo engine sequentially over chronologically sorted matches.

    `matches` must have columns: date, season, home_team, away_team,
    home_goals, away_goals (both goal columns numeric, no NaNs).
    `seed_ratings` optionally pre-seeds specific teams (e.g. the three
    2026-27 promoted clubs) rather than using the flat/offset default.
    `promoted_offset` is added to `INITIAL_RATING` for any team seen
    for the first time and not present in `seed_ratings`.
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    ratings: dict[str, float] = dict(seed_ratings or {})
    last_season: dict[str, str] = {}
    rows = []
    league_mean_records = []

    for _, m in matches.iterrows():
        home, away, season = m["home_team"], m["away_team"], m["season"]

        for team in (home, away):
            if team not in ratings:
                ratings[team] = INITIAL_RATING + promoted_offset
            elif last_season.get(team) not in (None, season):
                league_mean = sum(ratings.values()) / len(ratings)
                ratings[team] = ratings[team] * (1 - season_reversion) + league_mean * season_reversion
            last_season[team] = season

        r_home, r_away = ratings[home], ratings[away]
        home_goals, away_goals = int(m["home_goals"]), int(m["away_goals"])
        goal_diff = home_goals - away_goals

        expected_home = _expected_score(r_home + home_advantage, r_away)
        actual_home = 1.0 if goal_diff > 0 else (0.5 if goal_diff == 0 else 0.0)

        elo_diff_winner = (r_home + home_advantage - r_away) if goal_diff >= 0 else (r_away - (r_home + home_advantage))
        mult = _mov_multiplier(goal_diff, elo_diff_winner)

        delta = k_factor * mult * (actual_home - expected_home)
        new_home, new_away = r_home + delta, r_away - delta

        rows.append({
            "date": m["date"], "season": season, "home_team": home, "away_team": away,
            "home_elo_pre": r_home, "away_elo_pre": r_away,
            "home_elo_post": new_home, "away_elo_post": new_away,
            "expected_home_score": expected_home,
        })
        ratings[home], ratings[away] = new_home, new_away
        league_mean_records.append({"date": m["date"], "league_mean_elo": sum(ratings.values()) / len(ratings)})

    history = pd.DataFrame(rows)
    league_mean_by_date = pd.DataFrame(league_mean_records).set_index("date")["league_mean_elo"]
    return EloRun(history=history, final_ratings=ratings, league_mean_by_date=league_mean_by_date)


def compute_promoted_team_elo_offset(matches: pd.DataFrame) -> tuple[float, int]:
    """Empirically measure how far below the league mean promoted teams
    settle by the end of their debut season, using real historical data.

    Returns (mean_offset, n_promotion_events_observed). A negative
    offset means promoted teams typically end up below league-average
    strength, as expected.
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    seasons_in_order = list(dict.fromkeys(matches["season"]))

    pass1 = run_elo(matches, seed_ratings=None, promoted_offset=0.0)
    history = pass1.history

    teams_by_season: dict[str, set[str]] = {}
    for s in seasons_in_order:
        s_matches = matches[matches["season"] == s]
        teams_by_season[s] = set(s_matches["home_team"]) | set(s_matches["away_team"])

    offsets = []
    for i in range(1, len(seasons_in_order)):
        prev_s, cur_s = seasons_in_order[i - 1], seasons_in_order[i]
        promoted = teams_by_season[cur_s] - teams_by_season[prev_s]
        if not promoted:
            continue
        season_hist = history[history["season"] == cur_s]
        if season_hist.empty:
            continue
        # league-mean rating at the end of that season (average of all post-match ratings that season)
        end_ratings = {}
        for team in teams_by_season[cur_s]:
            team_rows = season_hist[(season_hist["home_team"] == team) | (season_hist["away_team"] == team)]
            if team_rows.empty:
                continue
            last_row = team_rows.iloc[-1]
            end_ratings[team] = (
                last_row["home_elo_post"] if last_row["home_team"] == team else last_row["away_elo_post"]
            )
        if not end_ratings:
            continue
        league_mean = sum(end_ratings.values()) / len(end_ratings)
        for team in promoted:
            if team in end_ratings:
                offsets.append(end_ratings[team] - league_mean)

    if not offsets:
        return 0.0, 0
    return sum(offsets) / len(offsets), len(offsets)
