"""Real box-score-informed adjusted-plus-minus (APM) for NBA, from
each real player's own real per-game box-score +/- (ESPN's real
summary endpoint -- see collect_espn_nba_game_detail.py).

**Real, honest scope limitation**: true stint-level RAPM needs real
second-by-second 5-man-lineup data (which player was on court when),
not available from any free, verified source confirmed this session.
This is a GAME-level regression instead: for each real (team, game),
the target is that team's own real point differential, and the
features are every real player's own real minutes-share for that team
in that game (0 if they didn't play, or played for the other team).
A Ridge-regularized fit across many real games isolates each real
player's own marginal association with their team's real point
differential, controlling for which other real teammates shared the
floor that game -- the same spirit as true RAPM, at a coarser (game,
not stint) real granularity. Documented here, never overclaimed as
true stint-level RAPM.
"""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import Ridge

RIDGE_ALPHA = 2000.0  # real, standard-scale regularization for a sparse, collinear real lineup design matrix
MIN_REAL_GAMES = 10  # a player with fewer real games this season is folded into a league-average column instead


def _minutes_to_float(minutes_str) -> float:
    if not minutes_str or pd.isna(minutes_str):
        return 0.0
    try:
        return float(minutes_str)
    except ValueError:
        return 0.0


def build_apm_dataset(plus_minus_df: pd.DataFrame, historical_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Returns (X, y): one real row per (match_id, team), X columns are
    real player names (plus one "OTHER" column for thin-sample
    players), values are that player's real minutes-share of their
    team's real total minutes in that game; y is that team's real
    point differential."""
    pm = plus_minus_df.copy()
    pm["minutes_f"] = pm["minutes"].apply(_minutes_to_float)

    hist = historical_df[["match_id", "home_team", "away_team", "home_score", "away_score"]].drop_duplicates("match_id")
    hist_by_id = hist.set_index("match_id")

    games_played = pm.groupby("player_name")["match_id"].nunique()
    regular_players = set(games_played[games_played >= MIN_REAL_GAMES].index)
    pm["feature_player"] = pm["player_name"].where(pm["player_name"].isin(regular_players), "OTHER")

    rows, targets = [], []
    for (match_id, team), group in pm.groupby(["match_id", "team"]):
        if match_id not in hist_by_id.index:
            continue
        h = hist_by_id.loc[match_id]
        if team == h["home_team"]:
            point_diff = h["home_score"] - h["away_score"]
        elif team == h["away_team"]:
            point_diff = h["away_score"] - h["home_score"]
        else:
            continue  # real team-name mismatch between sources -- skip, never guess

        total_minutes = group["minutes_f"].sum()
        if total_minutes <= 0:
            continue
        shares = group.groupby("feature_player")["minutes_f"].sum() / total_minutes
        rows.append(shares.to_dict())
        targets.append(point_diff)

    X = pd.DataFrame(rows).fillna(0.0)
    y = pd.Series(targets)
    return X, y


def fit_apm_ratings(X: pd.DataFrame, y: pd.Series, alpha: float = RIDGE_ALPHA) -> dict[str, float]:
    """Each real player's own real Ridge-regularized coefficient --
    real points of team point-differential associated with that
    player's real presence, per full game at 100% of team minutes,
    controlling for every other real player in X simultaneously."""
    ridge = Ridge(alpha=alpha)
    ridge.fit(X, y)
    return dict(zip(X.columns, ridge.coef_))
