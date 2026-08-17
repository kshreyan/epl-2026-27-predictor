"""Dynamic team-strength "state" for a given point in time.

Phase-1 scope: today (2026-08-18) is before kickoff, so there is no
2026-27 match data to update on yet -- this module produces the
**preseason baseline state** (matchweek=0). The weekly-update engine
(a later phase) re-invokes the same fit routine after each real
matchweek's results land, which is exactly how the "dynamic" part of
this state-space model is meant to operate: each call refits on all
real data available as of that moment (see
`src/models/scoreline_models.fit_dixon_coles_model`), warm-started
from the previous state for speed.

Team strength here is expressed as Dixon-Coles log-attack/log-defense
parameters (see scoreline_models.py), not raw goals -- higher attack
= scores more, higher defense = concedes less. A team's "net strength"
is attack - defense; the home-strength variant adds the fitted global
home-advantage term.

Uncertainty intervals: a full weighted-bootstrap refit was tried first
(resample matches, refit hundreds of times) but took ~27s per resample
in this environment -- too slow to run 200x. Instead we use a Laplace
(Hessian) approximation: the inverse of the second derivative of the
regularized negative log-likelihood at its minimum is the standard
asymptotic covariance estimate for a penalized MLE, computed from a
single fit. This naturally gives wider intervals to teams with little
or stale data (a team with zero matches in the window has curvature
coming only from the L2 regularization term, which is the loosest
possible constraint) and tighter intervals to well-observed teams --
so promoted teams end up with the wide uncertainty required by spec
section 12 without any separate ad-hoc widening step.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.models.scoreline_models import apply_promoted_team_adjustment, fit_dixon_coles_model
from src.utils.versioning import MODEL_VERSION, now_utc_iso

Z_90 = norm.ppf(0.95)  # for a symmetric 5th/95th percentile band


def _shrink(values: np.ndarray, indices: list[int], fraction: float) -> np.ndarray:
    out = values.copy()
    for i in indices:
        out[i] = out[i] * (1 - fraction)
    return out


def compute_team_strength_state(
    matches_df: pd.DataFrame,
    teams_universe: list[str],
    as_of_date: pd.Timestamp,
    promoted_teams: list[str],
    promoted_attack_offset: float,
    promoted_defense_offset: float,
    half_life_days: float = 425.0,
    shrinkage_to_league_prior: float = 0.20,
    promoted_extra_shrinkage: float = 0.35,
    matchweek: int = 0,
    l2_reg: float | None = None,
):
    fit = fit_dixon_coles_model(matches_df, teams_universe, as_of_date, half_life_days, l2_reg=l2_reg if l2_reg is not None else 0.03)
    fit = apply_promoted_team_adjustment(fit, promoted_teams, promoted_attack_offset, promoted_defense_offset)

    promoted_idx = [fit.team_index[t] for t in promoted_teams]
    non_promoted_idx = [i for i in range(len(teams_universe)) if i not in promoted_idx]

    attack = _shrink(fit.attack, non_promoted_idx, shrinkage_to_league_prior)
    attack = _shrink(attack, promoted_idx, shrinkage_to_league_prior + promoted_extra_shrinkage)
    defense = _shrink(fit.defense, non_promoted_idx, shrinkage_to_league_prior)
    defense = _shrink(defense, promoted_idx, shrinkage_to_league_prior + promoted_extra_shrinkage)

    attack_se = fit.attack_se if fit.attack_se is not None else np.full(len(teams_universe), np.nan)
    defense_se = fit.defense_se if fit.defense_se is not None else np.full(len(teams_universe), np.nan)

    generated_at = now_utc_iso()
    rows = []
    for team in teams_universe:
        i = fit.team_index[team]
        a_mean, d_mean = attack[i], defense[i]
        a_se, d_se = attack_se[i], defense_se[i]
        a_p05, a_p95 = a_mean - Z_90 * a_se, a_mean + Z_90 * a_se
        d_p05, d_p95 = d_mean - Z_90 * d_se, d_mean + Z_90 * d_se

        home_strength = a_mean - d_mean + fit.home_advantage
        away_strength = a_mean - d_mean
        uncertainty_score = float((a_p95 - a_p05) + (d_p95 - d_p05))

        rows.append({
            "team": team,
            "matchweek": matchweek,
            "attack_strength_mean": round(float(a_mean), 4),
            "attack_strength_p05": round(float(a_p05), 4),
            "attack_strength_p95": round(float(a_p95), 4),
            "defense_strength_mean": round(float(d_mean), 4),
            "defense_strength_p05": round(float(d_p05), 4),
            "defense_strength_p95": round(float(d_p95), 4),
            "home_strength_mean": round(float(home_strength), 4),
            "away_strength_mean": round(float(away_strength), 4),
            "uncertainty_score": round(uncertainty_score, 4),
            "is_promoted_team": team in promoted_teams,
            "model_version": MODEL_VERSION,
            "generated_at": generated_at,
        })

    return pd.DataFrame(rows), fit
