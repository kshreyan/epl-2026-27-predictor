"""Per-fighter Elo rating for UFC, fit on real historical fight results
(collect_espn_ufc_historical.py).

Deliberately NOT a reuse of elo_model.py's `run_elo` -- that engine is
built around a real goal/point MARGIN-of-victory multiplier and a real
home-field advantage, neither of which has a real analogue for an
individual fight (no score margin, no home/away -- a real neutral-site
framing throughout, confirmed directly: ESPN's own competitor "order"
field is a display convention, not a real home/away designation).
Forcing that engine to fit here would mean inventing a fake margin/
home-advantage signal; this is a plain win/loss Elo update instead,
the standard real form for an individual combat sport.

One real global rating per fighter, not one per weight class -- a
fighter who moves weight classes keeps their one real rating (a
disclosed simplification: cross-weight-class movement is real but
comparatively rare, and splitting ratings per class would fragment an
already comparatively small real per-fighter sample even further). The
real per-weight-class RANKINGS page (rank_ufc_fighters.py) groups
fighters by their most recent real weight class for DISPLAY only --
the rating itself is global.

A real draw (rare in UFC -- majority/unanimous/split draws all real,
confirmed in this project's own historical data) updates both
fighters' ratings toward each other (actual=0.5), the standard Elo
treatment, not excluded or treated as a non-event.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

INITIAL_RATING = 1500.0
K_FACTOR = 24.0


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_a - rating_b) / 400.0))


@dataclass
class FighterEloRun:
    history: pd.DataFrame            # one row per fight: pre-fight ratings for both fighters
    final_ratings: dict[str, float]  # fighter_id -> rating after the last fight in the input
    last_weight_class: dict[str, str]  # fighter_id -> most recent real weight class fought in


def run_fighter_elo(fights: pd.DataFrame, k_factor: float = K_FACTOR) -> FighterEloRun:
    """`fights` must have columns: date, fighter_a, fighter_b,
    winner (one of "fighter_a"/"fighter_b"/"draw"), weight_class,
    sorted or not (sorted internally)."""
    fights = fights.sort_values("date").reset_index(drop=True)
    ratings: dict[str, float] = {}
    last_weight_class: dict[str, str] = {}
    rows = []

    for _, fgt in fights.iterrows():
        a, b = fgt["fighter_a"], fgt["fighter_b"]
        r_a = ratings.setdefault(a, INITIAL_RATING)
        r_b = ratings.setdefault(b, INITIAL_RATING)

        expected_a = _expected_score(r_a, r_b)
        actual_a = 1.0 if fgt["winner"] == "fighter_a" else (0.0 if fgt["winner"] == "fighter_b" else 0.5)

        delta = k_factor * (actual_a - expected_a)
        new_a, new_b = r_a + delta, r_b - delta

        rows.append({
            "date": fgt["date"], "fighter_a": a, "fighter_b": b,
            "fighter_a_elo_pre": r_a, "fighter_b_elo_pre": r_b,
            "fighter_a_elo_post": new_a, "fighter_b_elo_post": new_b,
            "expected_fighter_a_win": expected_a,
        })
        ratings[a], ratings[b] = new_a, new_b
        last_weight_class[a] = fgt["weight_class"]
        last_weight_class[b] = fgt["weight_class"]

    history = pd.DataFrame(rows)
    return FighterEloRun(history=history, final_ratings=ratings, last_weight_class=last_weight_class)


def win_probability(rating_a: float, rating_b: float) -> float:
    """Real P(fighter A wins), read directly off the Elo expected-score
    formula -- the fight's real draw probability (rare, see
    fight_distance_model.py for where it's handled) is not modeled by
    this function; callers that need it combine this with a separately
    fit real draw rate."""
    return _expected_score(rating_a, rating_b)
