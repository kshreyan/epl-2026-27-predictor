"""Market-odds cleaning utilities (spec section 17).

No live odds feed is connected in Phase 1/2 (see
config/data_sources.yaml), so `build_market_features` currently
produces `market_available=False` rows for every fixture. The cleaning
math itself -- overround removal and log-odds (logit) averaging across
bookmakers -- is real, fully implemented, and unit-tested
(tests/test_market_odds_cleaning.py) against synthetic odds, so it is
ready to use the moment a real odds feed is wired in without further
changes to this module.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def remove_overround(decimal_odds: tuple[float, float, float]) -> tuple[float, float, float]:
    """Converts 1X2 decimal odds to no-vig (overround-removed) probabilities
    via simple proportional normalization of the raw implied probabilities.
    """
    raw = [1.0 / o for o in decimal_odds]
    total = sum(raw)
    return tuple(r / total for r in raw)


def overround(decimal_odds: tuple[float, float, float]) -> float:
    """The bookmaker's margin: sum of raw implied probabilities minus 1
    (0 = a fair book, >0 = the house edge)."""
    return sum(1.0 / o for o in decimal_odds) - 1.0


def _logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


def _inv_logit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def log_odds_average(probability_triples: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    """Aggregates multiple bookmakers' no-vig 1X2 probabilities by averaging
    in logit space (more standard for probability aggregation than a plain
    arithmetic mean, since it respects the multiplicative nature of odds),
    then renormalizes the three classes to sum to 1.
    """
    if not probability_triples:
        raise ValueError("no probability triples to average")
    arr = np.array(probability_triples)  # shape (n_bookmakers, 3)
    logits = np.vectorize(_logit)(arr)
    mean_logits = logits.mean(axis=0)
    probs = np.vectorize(_inv_logit)(mean_logits)
    probs = probs / probs.sum()
    return tuple(probs.tolist())


def build_market_features(odds_df: pd.DataFrame) -> pd.DataFrame:
    """One row per match_id with market_available and (when real odds
    exist) cleaned market probabilities. With the current sentinel-only
    epl_2026_27_real_odds.csv, every row is market_available=False."""
    rows = []
    for match_id, group in odds_df.groupby("match_id"):
        real_rows = group[group["is_real_data"] == True]  # noqa: E712
        if real_rows.empty:
            rows.append({
                "match_id": match_id,
                "market_available": False,
                "market_home_win_prob_current": "",
                "market_draw_prob_current": "",
                "market_away_win_prob_current": "",
                "market_overround": "",
                "market_favorite": "",
                "market_entropy": "",
            })
            continue

        triples = []
        overrounds = []
        for _, r in real_rows.iterrows():
            odds = (float(r["current_home_odds"]), float(r["current_draw_odds"]), float(r["current_away_odds"]))
            triples.append(remove_overround(odds))
            overrounds.append(overround(odds))

        h, d, a = log_odds_average(triples)
        probs = {"home": h, "draw": d, "away": a}
        favorite = max(probs, key=probs.get)
        entropy = -sum(p * math.log(p) for p in probs.values() if p > 0)

        rows.append({
            "match_id": match_id,
            "market_available": True,
            "market_home_win_prob_current": round(h, 4),
            "market_draw_prob_current": round(d, 4),
            "market_away_win_prob_current": round(a, 4),
            "market_overround": round(float(np.mean(overrounds)), 4),
            "market_favorite": favorite,
            "market_entropy": round(entropy, 4),
        })
    return pd.DataFrame(rows)
