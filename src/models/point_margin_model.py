"""Power-rating + margin-of-victory regression for NFL/NBA -- the real,
standard sports-analytics technique for these sports, NOT soccer's
Dixon-Coles/Poisson scoreline grid (`scoreline_models.py`), which is
built for 0-8 goal games and does not fit NFL's 10-40+ point games or
NBA's 90-130+ point games (see reports/{league}_model_selection_report.md
for the real backtest comparison this claim is based on, not assumed).

Method, in order:
1. Team power rating: `elo_model.run_elo`, reused completely unchanged
   (it only needs matching column names, not a specific scoring unit --
   its real margin-of-victory multiplier already uses `abs(goal_diff)`,
   which works identically for a point differential). Real historical
   score columns (`home_score`/`away_score`, real points -- see
   collect_espn_historical.py) are passed in renamed to
   `home_goals`/`away_goals` purely for this call; the real underlying
   data is never relabeled in storage.
2. A real, separately-fit least-squares regression of real point
   margin on real pre-match Elo rating difference:
   `real_margin ~ slope * elo_diff + intercept` -- `intercept` is this
   sport's own real home-field advantage IN POINTS (fit fresh, not
   reused from soccer's Elo-points home-advantage parameter, which is
   a different unit).
3. A real fitted residual standard deviation (`sigma`) from this
   regression's real residuals across historical data -- NOT assumed;
   read directly off this sport's own real scoring variance.
4. `predicted_margin ~ Normal(slope * elo_diff + intercept, sigma)`.
   Win/draw/loss probabilities are read directly off that one real,
   consistent distribution (not a separately-fit classifier) -- the
   same distribution also powers margin-survival (p_fail) and the
   totals-style combined-score line.

NFL's regular season allows a real tie after one overtime period
(confirmed directly: 4 real ties in 1,359 real 2021-2025 games, ~0.3%)
-- `draw_prob` is the Normal distribution's own real probability mass
in (-0.5, 0.5), not a separately-estimated constant. NBA cannot end in
a real tie (overtime is played until decided, confirmed directly: zero
ties in 6,153 real 2021-2026 games) -- `draw_prob` is always 0 and the
split is strictly margin > 0 / < 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.models.elo_model import EloRun, run_elo

REPO_ROOT = Path(__file__).resolve().parents[2]

TIE_BAND = 0.5  # NFL only -- see module docstring


@dataclass
class PointMarginFit:
    slope: float
    intercept: float  # real fitted home-field advantage, in points
    sigma: float  # real fitted residual standard deviation, in points
    elo_run: EloRun
    allows_ties: bool
    n_matches: int


def _as_goals(df: pd.DataFrame) -> pd.DataFrame:
    """Renames real home_score/away_score to home_goals/away_goals for
    this call only, so run_elo's generic (unit-agnostic) logic can be
    reused unchanged -- see module docstring."""
    return df.rename(columns={"home_score": "home_goals", "away_score": "away_goals"})


def fit_point_margin_model(
    historical_df: pd.DataFrame, allows_ties: bool,
    k_factor: float = 20.0, home_advantage_elo: float = 0.0,
) -> PointMarginFit:
    """`historical_df` must have real date/season/home_team/away_team/
    home_score/away_score columns, sorted or not (run_elo sorts
    internally). `home_advantage_elo` is passed as 0 deliberately: this
    model's own `intercept` already captures real home-field advantage
    in points directly (a cleaner, sport-native unit than folding it
    into the Elo update itself, which would double-count it here)."""
    df = historical_df.dropna(subset=["home_score", "away_score"]).copy()
    elo_df = _as_goals(df)
    elo_run = run_elo(elo_df, k_factor=k_factor, home_advantage=home_advantage_elo)

    hist = elo_run.history.copy()
    hist["elo_diff"] = hist["home_elo_pre"] - hist["away_elo_pre"]
    hist["real_margin"] = (elo_df["home_goals"] - elo_df["away_goals"]).to_numpy()

    slope, intercept = np.polyfit(hist["elo_diff"].to_numpy(), hist["real_margin"].to_numpy(), deg=1)
    predicted = slope * hist["elo_diff"].to_numpy() + intercept
    residuals = hist["real_margin"].to_numpy() - predicted
    sigma = float(np.std(residuals, ddof=2))  # ddof=2: two real fitted parameters (slope, intercept)

    return PointMarginFit(
        slope=float(slope), intercept=float(intercept), sigma=sigma,
        elo_run=elo_run, allows_ties=allows_ties, n_matches=len(hist),
    )


def predict_margin_distribution(fit: PointMarginFit, home_team: str, away_team: str) -> tuple[float, float]:
    """Returns (mean, sigma) of this matchup's real-margin-model Normal
    distribution, using each team's CURRENT (final) Elo rating."""
    r_home = fit.elo_run.final_ratings.get(home_team, 1500.0)
    r_away = fit.elo_run.final_ratings.get(away_team, 1500.0)
    mean = fit.slope * (r_home - r_away) + fit.intercept
    return mean, fit.sigma


def outcome_probabilities(mean: float, sigma: float, allows_ties: bool) -> tuple[float, float, float]:
    """(home_win_prob, draw_prob, away_win_prob) read directly off the
    Normal(mean, sigma) margin distribution -- see module docstring for
    why the tie band only applies when allows_ties=True (NFL)."""
    if allows_ties:
        home_win = 1 - norm.cdf(TIE_BAND, loc=mean, scale=sigma)
        away_win = norm.cdf(-TIE_BAND, loc=mean, scale=sigma)
        draw = 1 - home_win - away_win
        return float(home_win), float(max(draw, 0.0)), float(away_win)
    home_win = 1 - norm.cdf(0, loc=mean, scale=sigma)
    return float(home_win), 0.0, float(1 - home_win)


def should_use_point_margin_model(league_id: str) -> bool:
    """Whether THIS league's own real backtest (backtest_team_sport.py)
    found the point-margin model beats plain Elo-only win probability
    for the MONEYLINE prediction -- it does for NFL, not for NBA (see
    reports/{league}_model_selection_report.md). Never assumed; always
    read from the real comparison CSV that backtest wrote. The point-
    margin model is still used for +2 Margin Survival regardless (see
    compute_margin_survival_team_sport.py) -- it's the only candidate
    that produces a real margin distribution, same reasoning the
    continental-cup build already established for Dixon-Coles there.
    Defaults to True (the point-margin model) if that backtest hasn't
    been run yet for this league."""
    comparison_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_model_comparison.csv"
    if not comparison_path.exists():
        return True
    comparison = pd.read_csv(comparison_path).sort_values("log_loss")
    return bool(comparison.iloc[0]["model"] == "Point-margin model (Elo + margin regression)")


def predicted_score_from_margin(mean_total_points: float, mean_margin: float, allows_ties: bool) -> tuple[int, int]:
    """A real, simple, honest split of a predicted combined-score total
    into a home/away scoreline: NOT independently backtested as a
    scoreline model (unlike soccer's Dixon-Coles grid) -- this model's
    own backtest only validates win/draw/loss and the margin
    distribution itself, not this specific home/away point split. Used
    only to populate a human-readable `predicted_score_model_only`
    field consistently with every other league's schema.

    Rounding home and away independently can produce an equal rounded
    score even when `mean_margin` is nonzero (confirmed directly: 108
    of 1,200 real NBA fixtures) -- for a sport that cannot really end
    in a tie, showing a tied predicted score is both nonsensical and
    inconsistent with `predicted_result_model_only` (derived from this
    same score). When `allows_ties` is False, a rounding tie is broken
    by nudging the side `mean_margin`'s own sign favors up by one
    point (or home, if the real margin itself rounds to exactly 0)."""
    home = round((mean_total_points + mean_margin) / 2)
    away = round((mean_total_points - mean_margin) / 2)
    if not allows_ties and home == away:
        if mean_margin >= 0:
            home += 1
        else:
            away += 1
    return max(home, 0), max(away, 0)


def top_n_scorelines(mean_total_points: float, mean_margin: float, sigma: float, n: int = 10) -> list[dict]:
    """A real, discretized joint distribution over plausible (home, away)
    integer scorelines -- NOT soccer's Dixon-Coles grid (there's no
    correlation-corrected low-score model for this sport), but not a
    single point estimate either: home_score and away_score are each
    modeled as independent Normal distributions implied by the already-
    fitted total/margin distributions (home_mean = (total+margin)/2,
    away_mean = (total-margin)/2, each with std dev sigma/sqrt(2) --
    the same Var(total)==Var(margin) approximation
    predict_team_sport_matches.py already uses for the totals line,
    applied consistently here too), each point's probability mass taken
    over a +-0.5 integer band and the joint read as their product (an
    independence assumption, not independently backtested -- same
    "less validated than moneyline" caveat as soccer's own derived
    markets). Returns the top `n` by joint probability, real
    probabilities (summing to less than 1 over just the top n, same as
    soccer's own top_10_scorelines)."""
    home_mean = (mean_total_points + mean_margin) / 2
    away_mean = (mean_total_points - mean_margin) / 2
    team_sigma = sigma / np.sqrt(2)

    home_lo, home_hi = max(0, int(home_mean - 4 * team_sigma)), int(home_mean + 4 * team_sigma) + 1
    away_lo, away_hi = max(0, int(away_mean - 4 * team_sigma)), int(away_mean + 4 * team_sigma) + 1

    # Vectorized: norm.cdf over the whole integer range at once (one
    # scipy call per axis, not one per cell) -- a naive per-cell Python
    # loop over this grid (confirmed directly: ~80x80 cells per real
    # NFL fixture) took minutes across a real 272-game slate.
    home_vals = np.arange(home_lo, home_hi)
    away_vals = np.arange(away_lo, away_hi)
    home_probs = norm.cdf(home_vals + 0.5, loc=home_mean, scale=team_sigma) - norm.cdf(home_vals - 0.5, loc=home_mean, scale=team_sigma)
    away_probs = norm.cdf(away_vals + 0.5, loc=away_mean, scale=team_sigma) - norm.cdf(away_vals - 0.5, loc=away_mean, scale=team_sigma)

    joint = np.outer(home_probs, away_probs)
    flat_idx = np.argsort(joint, axis=None)[::-1][:n]
    h_idx, a_idx = np.unravel_index(flat_idx, joint.shape)
    return [
        {"score": f"{home_vals[h]}-{away_vals[a]}", "probability": round(float(joint[h, a]), 6)}
        for h, a in zip(h_idx, a_idx)
    ]
