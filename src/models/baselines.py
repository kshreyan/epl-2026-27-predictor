"""Honest, simple benchmark models the main Dixon-Coles/Elo system must
beat to justify its extra complexity (spec section 18).

All four baselines are fit only on real historical data available
before the match being predicted -- no leakage.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def previous_season_table_baseline(
    matches_df: pd.DataFrame, home_team: str, away_team: str, season: str,
) -> tuple[float, float, float]:
    """Win/draw/away probabilities from a logistic function of each team's
    final rank in the season immediately before `season`. Falls back to
    a flat 33/33/33 split when either team has no known previous-season
    rank (e.g. a promoted club)."""
    seasons_sorted = sorted(matches_df["season"].unique())
    try:
        idx = seasons_sorted.index(season)
    except ValueError:
        idx = len(seasons_sorted)
    if idx == 0:
        return (1 / 3, 1 / 3, 1 / 3)
    prev_season = seasons_sorted[idx - 1]
    prev = matches_df[matches_df["season"] == prev_season].dropna(subset=["home_goals", "away_goals"])
    if prev.empty:
        return (1 / 3, 1 / 3, 1 / 3)

    teams = sorted(set(prev["home_team"]) | set(prev["away_team"]))
    pts = {t: 0 for t in teams}
    for _, m in prev.iterrows():
        h, a, hg, ag = m["home_team"], m["away_team"], m["home_goals"], m["away_goals"]
        if hg > ag:
            pts[h] += 3
        elif hg < ag:
            pts[a] += 3
        else:
            pts[h] += 1
            pts[a] += 1
    ranking = {t: r + 1 for r, t in enumerate(sorted(pts, key=lambda t: -pts[t]))}

    if home_team not in ranking or away_team not in ranking:
        return (1 / 3, 1 / 3, 1 / 3)

    rank_diff = ranking[away_team] - ranking[home_team]  # positive => home team ranked higher (smaller number)
    home_edge = 1 / (1 + math.exp(-0.15 * rank_diff))
    home_win = 0.30 + 0.35 * home_edge
    away_win = 0.30 + 0.35 * (1 - home_edge)
    draw = max(1 - home_win - away_win, 0.05)
    total = home_win + draw + away_win
    return (home_win / total, draw / total, away_win / total)


def elo_only_probabilities(elo_home: float, elo_away: float, home_advantage: float = 60.0) -> tuple[float, float, float]:
    """1X2 probabilities from an Elo rating difference alone, using the
    standard logistic win-expectancy curve plus a draw band calibrated
    to typical EPL draw rates (~24%)."""
    expected_home = 1 / (1 + 10 ** (-(elo_home + home_advantage - elo_away) / 400))
    draw_prob = 0.24 - 0.08 * abs(expected_home - 0.5) * 2
    draw_prob = max(0.12, min(0.30, draw_prob))
    home_win = expected_home * (1 - draw_prob)
    away_win = (1 - expected_home) * (1 - draw_prob)
    return (home_win, draw_prob, away_win)


def simple_poisson_baseline(
    home_avg_gf: float, home_avg_ga: float, away_avg_gf: float, away_avg_ga: float,
    league_avg_goals: float,
) -> tuple[float, float]:
    """Very simple attack/defense-strength Poisson baseline (no Dixon-Coles
    low-score correlation correction, no time-decay), the classic
    "textbook" football Poisson model."""
    if league_avg_goals <= 0:
        league_avg_goals = 1.35
    home_attack_strength = home_avg_gf / league_avg_goals
    home_defense_strength = home_avg_ga / league_avg_goals
    away_attack_strength = away_avg_gf / league_avg_goals
    away_defense_strength = away_avg_ga / league_avg_goals
    lam = home_attack_strength * away_defense_strength * league_avg_goals
    mu = away_attack_strength * home_defense_strength * league_avg_goals
    return max(lam, 0.05), max(mu, 0.05)


def promoted_team_historical_baseline(promoted_summary: dict, n_teams: int = 20) -> tuple[float, float, float]:
    """Uses the real historical promoted-team relegation rate/points
    shortfall (src/models/promoted_team_adjustment.py) to give a
    promoted team a fixed, data-derived (not guessed) below-average
    win probability whenever it plays, regardless of opponent -- a
    deliberately crude baseline, only meant as a floor to beat."""
    if not promoted_summary.get("mean_points"):
        return (0.30, 0.26, 0.44)
    mean_points = promoted_summary["mean_points"]
    ppg = mean_points / 38.0
    implied_win_rate = max(0.10, min(0.45, ppg / 3.0))
    draw_rate = 0.24
    loss_rate = 1 - implied_win_rate - draw_rate
    return (implied_win_rate, draw_rate, loss_rate)
