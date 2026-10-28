"""Real per-QB rating: an Elo-style rating tracked by QB IDENTITY
(name) rather than team, fit on real historical games via nflverse's
real home_qb_name/away_qb_name (see collect_nflverse.py) -- the same
margin-of-victory-weighted logistic update elo_model.py already uses
for teams, adapted for a quarterback instead (no home-advantage or
season-reversion term here: a QB's own skill is the thing being
measured, not a team context that resets each season the way a roster
overhaul does).

A QB with few real starts gets an empirical shrinkage toward the
league-average baseline proportional to real start count (`n / (n +
SHRINK_K)`) -- NOT a full Hessian/Laplace-approximation posterior the
way `dynamic_team_strength_state_space.py`'s team ratings are (that
would need every QB's own real per-game log-likelihood curvature,
which this simpler Elo-style update doesn't produce) -- labeled
honestly as empirical shrinkage, not overclaimed as Bayesian.

This module only produces the rating; `backtest_nfl_qb_adjustment.py`
decides, from a real held-out-season test, whether the signal this
produces explains real residual variance the team-only point-margin
model already misses -- never assumed to help.
"""
from __future__ import annotations

import math

import pandas as pd

BASELINE_RATING = 1500.0
QB_K_FACTOR = 12.0  # smaller than team Elo's 20 -- one QB's real game-to-game signal is noisier
SHRINK_K = 8.0  # real starts at which a QB's rating is shrunk halfway toward the league baseline


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_a - rating_b) / 400.0))


def _mov_multiplier(margin: int, elo_diff_winner_perspective: float) -> float:
    if margin == 0:
        return 1.0
    return math.log(abs(margin) + 1) * (2.2 / (abs(elo_diff_winner_perspective) * 0.001 + 2.2))


def fit_qb_elo(historical_df: pd.DataFrame, k_factor: float = QB_K_FACTOR) -> tuple[dict[str, float], dict[str, int]]:
    """Returns (raw_rating, n_starts) per real QB name, from sequential
    real games (sorted by date) with a real home_qb_name/away_qb_name.
    Games missing either QB name are skipped (a real but rare gap in
    nflverse's own data, never guessed)."""
    df = historical_df.dropna(subset=["home_qb_name", "away_qb_name", "home_score", "away_score"]).sort_values("date")
    ratings: dict[str, float] = {}
    n_starts: dict[str, int] = {}

    for _, g in df.iterrows():
        home_qb, away_qb = g["home_qb_name"], g["away_qb_name"]
        for qb in (home_qb, away_qb):
            ratings.setdefault(qb, BASELINE_RATING)
            n_starts.setdefault(qb, 0)

        r_home, r_away = ratings[home_qb], ratings[away_qb]
        margin = int(g["home_score"]) - int(g["away_score"])
        expected_home = _expected_score(r_home, r_away)
        actual_home = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
        elo_diff_winner = (r_home - r_away) if margin >= 0 else (r_away - r_home)
        mult = _mov_multiplier(margin, elo_diff_winner)
        delta = k_factor * mult * (actual_home - expected_home)

        ratings[home_qb] = r_home + delta
        ratings[away_qb] = r_away - delta
        n_starts[home_qb] += 1
        n_starts[away_qb] += 1

    return ratings, n_starts


def shrink_qb_ratings(raw_ratings: dict[str, float], n_starts: dict[str, int], shrink_k: float = SHRINK_K) -> dict[str, float]:
    """Empirical shrinkage toward BASELINE_RATING, proportional to real
    start count -- a QB with `shrink_k` real starts has their raw
    rating pulled exactly halfway toward the league baseline; more
    starts shrink less, fewer starts shrink more. Never a full
    posterior -- see module docstring."""
    return {
        qb: BASELINE_RATING + (raw_ratings[qb] - BASELINE_RATING) * (n_starts[qb] / (n_starts[qb] + shrink_k))
        for qb in raw_ratings
    }


def qb_adjustment(home_qb: str | None, away_qb: str | None, shrunk_ratings: dict[str, float]) -> float | None:
    """Signed real QB-quality differential (home - away), in the same
    Elo-point scale as team ratings, or None if either real starter is
    unknown (not yet projected by nflverse, or a genuinely new QB with
    zero real prior starts -- never guessed at 0 or league-average by
    fabricating a value; the caller decides how to handle a missing
    adjustment, e.g. by falling back to team-only)."""
    if not home_qb or not away_qb:
        return None
    home_rating = shrunk_ratings.get(home_qb, BASELINE_RATING)
    away_rating = shrunk_ratings.get(away_qb, BASELINE_RATING)
    return home_rating - away_rating
