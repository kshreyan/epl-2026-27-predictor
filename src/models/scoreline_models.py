"""Dixon-Coles bivariate-adjusted independent-Poisson scoreline model.

Implements Dixon & Coles (1997): two independent Poisson processes for
home/away goals, each driven by attack/defense strength and a home-
advantage term, plus a low-score correlation correction (`rho`) for
the 0-0/1-0/0-1/1-1 cells where independent Poisson underestimates the
real draw/one-goal-game frequency.

Fit by maximum likelihood with exponential time-decay weighting
(recent matches matter more) and a light L2 ridge penalty on
attack/defense, which keeps the model well-posed for teams with very
few (or, for a brand-new club like Coventry City in 2026-27, zero)
matches in the training window -- such teams are pulled to
league-average strength rather than left undefined.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

L2_REG = 0.03
RHO_INIT = -0.10
MAX_GOALS_GRID = 8  # scoreline surface covers 0-0 .. 8-8 (spec minimum: 0-0..7-7)


@dataclass
class DixonColesFit:
    teams: list[str]
    team_index: dict[str, int]
    attack: np.ndarray
    defense: np.ndarray
    home_advantage: float
    rho: float
    converged: bool
    n_matches_used: int
    effective_sample_size: float  # sum of time-decay weights
    theta_vector: np.ndarray = field(default=None)  # for warm-starting the next refit
    attack_se: np.ndarray = field(default=None)      # Laplace-approx standard errors
    defense_se: np.ndarray = field(default=None)


def _time_weights(days_before_as_of: np.ndarray, half_life_days: float) -> np.ndarray:
    decay_rate = math.log(2) / half_life_days
    return np.exp(-decay_rate * np.clip(days_before_as_of, 0, None))


def fit_dixon_coles(
    dates: np.ndarray,
    home_idx: np.ndarray,
    away_idx: np.ndarray,
    home_goals: np.ndarray,
    away_goals: np.ndarray,
    n_teams: int,
    as_of_date,
    half_life_days: float = 425.0,
    l2_reg: float = L2_REG,
    rho_init: float = RHO_INIT,
    warm_start_theta: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, float, float, bool, float, np.ndarray, np.ndarray]:
    """Core numeric fit. Returns (attack, defense, home_adv, rho, converged)."""
    days_before = np.array([(as_of_date - d).days for d in dates], dtype=float)
    weights = _time_weights(days_before, half_life_days)

    hg = home_goals.astype(float)
    ag = away_goals.astype(float)

    def unpack(theta):
        home_adv = theta[0]
        rho = theta[1]
        attack = theta[2:2 + n_teams]
        defense = theta[2 + n_teams:2 + 2 * n_teams]
        return home_adv, rho, attack, defense

    def negative_log_likelihood(theta):
        home_adv, rho, attack, defense = unpack(theta)
        lam = np.exp(home_adv + attack[home_idx] - defense[away_idx])
        mu = np.exp(attack[away_idx] - defense[home_idx])
        lam = np.clip(lam, 1e-6, 30)
        mu = np.clip(mu, 1e-6, 30)

        ll_home = hg * np.log(lam) - lam - _log_factorial(hg)
        ll_away = ag * np.log(mu) - mu - _log_factorial(ag)

        tau = np.ones_like(lam)
        m00 = (hg == 0) & (ag == 0)
        m01 = (hg == 0) & (ag == 1)
        m10 = (hg == 1) & (ag == 0)
        m11 = (hg == 1) & (ag == 1)
        tau = np.where(m00, 1 - lam * mu * rho, tau)
        tau = np.where(m01, 1 + lam * rho, tau)
        tau = np.where(m10, 1 + mu * rho, tau)
        tau = np.where(m11, 1 - rho, tau)
        tau = np.clip(tau, 1e-6, None)

        ll = weights * (ll_home + ll_away + np.log(tau))
        reg = l2_reg * (np.sum(attack ** 2) + np.sum(defense ** 2))
        return -np.sum(ll) + reg

    if warm_start_theta is not None and len(warm_start_theta) == 2 + 2 * n_teams:
        theta0 = warm_start_theta.copy()
    else:
        theta0 = np.zeros(2 + 2 * n_teams)
        theta0[0] = 0.3  # home_adv starting guess (log scale, ~ +35% goal rate at home)
        theta0[1] = rho_init

    result = minimize(negative_log_likelihood, theta0, method="L-BFGS-B", options={"maxiter": 300})
    home_adv, rho, attack, defense = unpack(result.x)

    # Laplace (Hessian) approximation to parameter uncertainty, computed in
    # closed form rather than via L-BFGS-B's returned hess_inv (which is a
    # low-rank limited-memory approximation built during optimization and
    # is not an accurate curvature estimate for a 70+ parameter problem --
    # confirmed empirically: it gave near-identical, badly-scaled intervals
    # for a heavily-observed team like Arsenal and a zero-history team like
    # Coventry City). A full bootstrap refit was tried first and was too
    # slow (~27s per resample) to run hundreds of times in this environment.
    #
    # For a Poisson log-link model, d2(NLL)/dz2 = lambda where z is the
    # linear predictor, so the diagonal curvature contribution of each
    # match to attack[home]/defense[away] (which both enter lam's linear
    # predictor with coefficient +-1) is exactly weight*lam, and to
    # attack[away]/defense[home] is weight*mu. This ignores the small tau
    # (rho) correction curvature and cross-team covariance, but correctly
    # differentiates well-observed teams (curvature dominated by real
    # matches) from unobserved/promoted teams (curvature from the L2
    # regularization term alone, i.e. the widest possible band).
    lam_fit = np.clip(np.exp(home_adv + attack[home_idx] - defense[away_idx]), 1e-6, 30)
    mu_fit = np.clip(np.exp(attack[away_idx] - defense[home_idx]), 1e-6, 30)

    diag_attack = np.full(n_teams, 2 * l2_reg)
    diag_defense = np.full(n_teams, 2 * l2_reg)
    np.add.at(diag_attack, home_idx, weights * lam_fit)
    np.add.at(diag_attack, away_idx, weights * mu_fit)
    np.add.at(diag_defense, away_idx, weights * lam_fit)
    np.add.at(diag_defense, home_idx, weights * mu_fit)

    attack_se = np.sqrt(1.0 / diag_attack)
    defense_se = np.sqrt(1.0 / diag_defense)
    param_se = np.concatenate([[np.nan, np.nan], attack_se, defense_se])

    return attack, defense, float(home_adv), float(rho), bool(result.success), weights.sum(), result.x, param_se


def _log_factorial(x: np.ndarray) -> np.ndarray:
    return np.array([math.lgamma(v + 1) for v in x])


def fit_dixon_coles_model(
    matches_df,
    teams_universe: list[str],
    as_of_date,
    half_life_days: float = 425.0,
    warm_start: "DixonColesFit | None" = None,
    l2_reg: float = L2_REG,
    rho_init: float = RHO_INIT,
) -> DixonColesFit:
    team_index = {t: i for i, t in enumerate(teams_universe)}
    df = matches_df[matches_df["home_team"].isin(team_index) & matches_df["away_team"].isin(team_index)].copy()
    df = df.dropna(subset=["home_goals", "away_goals"])

    dates = df["date"].to_numpy()
    home_idx = df["home_team"].map(team_index).to_numpy()
    away_idx = df["away_team"].map(team_index).to_numpy()
    home_goals = df["home_goals"].astype(int).to_numpy()
    away_goals = df["away_goals"].astype(int).to_numpy()

    warm_theta = warm_start.theta_vector if (warm_start is not None and warm_start.teams == teams_universe) else None

    attack, defense, home_adv, rho, converged, ess, theta, param_se = fit_dixon_coles(
        dates, home_idx, away_idx, home_goals, away_goals,
        n_teams=len(teams_universe), as_of_date=as_of_date, half_life_days=half_life_days,
        l2_reg=l2_reg, rho_init=rho_init, warm_start_theta=warm_theta,
    )
    n = len(teams_universe)
    attack_se = param_se[2:2 + n]
    defense_se = param_se[2 + n:2 + 2 * n]
    return DixonColesFit(
        teams=teams_universe, team_index=team_index, attack=attack, defense=defense,
        home_advantage=home_adv, rho=rho, converged=converged,
        n_matches_used=len(df), effective_sample_size=float(ess), theta_vector=theta,
        attack_se=attack_se, defense_se=defense_se,
    )


def apply_promoted_team_adjustment(
    fit: DixonColesFit, promoted_teams: list[str], attack_offset: float, defense_offset: float,
) -> DixonColesFit:
    """Shift a promoted team's attack/defense parameters by an empirically
    observed offset (see src/models/promoted_team_adjustment.py) instead
    of leaving zero-history teams at raw league-average strength."""
    attack = fit.attack.copy()
    defense = fit.defense.copy()
    for team in promoted_teams:
        idx = fit.team_index[team]
        attack[idx] += attack_offset
        defense[idx] += defense_offset
    n = len(fit.teams)
    theta = np.concatenate([[fit.home_advantage, fit.rho], attack, defense])
    return DixonColesFit(
        teams=fit.teams, team_index=fit.team_index, attack=attack, defense=defense,
        home_advantage=fit.home_advantage, rho=fit.rho, converged=fit.converged,
        n_matches_used=fit.n_matches_used, effective_sample_size=fit.effective_sample_size,
        theta_vector=theta, attack_se=fit.attack_se, defense_se=fit.defense_se,
    )


def score_matrix(lam: float, mu: float, rho: float, max_goals: int = MAX_GOALS_GRID) -> np.ndarray:
    goals = np.arange(0, max_goals + 1)
    p_home = poisson.pmf(goals, lam)
    p_away = poisson.pmf(goals, mu)
    matrix = np.outer(p_home, p_away)

    for x, y in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        if x == 0 and y == 0:
            tau = 1 - lam * mu * rho
        elif x == 0 and y == 1:
            tau = 1 + lam * rho
        elif x == 1 and y == 0:
            tau = 1 + mu * rho
        else:
            tau = 1 - rho
        matrix[x, y] *= max(tau, 1e-6)

    matrix = matrix / matrix.sum()
    return matrix


def match_lambdas(fit: DixonColesFit, home_team: str, away_team: str) -> tuple[float, float]:
    h, a = fit.team_index[home_team], fit.team_index[away_team]
    lam = math.exp(fit.home_advantage + fit.attack[h] - fit.defense[a])
    mu = math.exp(fit.attack[a] - fit.defense[h])
    return lam, mu


def outcome_probabilities(matrix: np.ndarray) -> tuple[float, float, float]:
    home_win = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, 1).sum())
    return home_win, draw, away_win


def btts_probability(matrix: np.ndarray) -> float:
    """P(both teams score) -- both home and away goals >= 1."""
    return float(matrix[1:, 1:].sum())


def total_goals_probabilities(matrix: np.ndarray, line: float) -> tuple[float, float]:
    """P(total goals > line), P(total goals < line). A real total-goals
    market line is always a half-integer (e.g. 2.5), so no push is
    possible and the two probabilities always sum to 1."""
    n = matrix.shape[0]
    over = 0.0
    for i in range(n):
        for j in range(n):
            if i + j > line:
                over += matrix[i, j]
    return over, 1.0 - over


def asian_handicap_home_cover_probability(matrix: np.ndarray, home_line: float) -> float:
    """P(home side covers `home_line`), where home_line is added to the
    home team's goals -- e.g. home_line=-0.5 means home must win
    outright to cover; home_line=+0.5 means home covers on a draw or a
    home win. Away side's cover probability is `1 - this value` for a
    half/whole line (no push possible), or computed the same way with
    `-home_line` for a push-capable whole-number line.

    Real Asian Handicap markets also use quarter lines (e.g. -0.75),
    which split the stake across the two adjacent half-point lines
    rather than settling as one clean bet. Reported here as the
    average of the two adjacent lines' cover probabilities -- the
    standard simplification for a single reportable probability. At a
    whole-number line, a push (goal difference exactly cancels the
    line) is treated as half a cover, matching how a push returns the
    stake rather than winning or losing it."""
    doubled = home_line * 2
    if abs(doubled - round(doubled)) > 1e-9:  # a quarter line, e.g. -0.75
        lower = math.floor(doubled) / 2
        upper = lower + 0.5
        return (
            asian_handicap_home_cover_probability(matrix, lower)
            + asian_handicap_home_cover_probability(matrix, upper)
        ) / 2

    n = matrix.shape[0]
    cover, push = 0.0, 0.0
    for i in range(n):
        for j in range(n):
            diff = (i - j) + home_line
            if diff > 1e-9:
                cover += matrix[i, j]
            elif diff >= -1e-9:
                push += matrix[i, j]
    return cover + push * 0.5


def model_fair_handicap_line(matrix: np.ndarray) -> float:
    """The quarter-point handicap line closest to a genuine 50/50 cover
    probability for the home side -- the model's own "what line would
    make this a coin flip" answer, used as a default when no real
    market line is available for this fixture (most of the season)."""
    candidates = [x / 4 for x in range(-16, 17)]  # -4.00 to +4.00 in quarter-goal steps
    best_line, best_gap = 0.0, 1.0
    for line in candidates:
        gap = abs(asian_handicap_home_cover_probability(matrix, line) - 0.5)
        if gap < best_gap:
            best_gap, best_line = gap, line
    return best_line


def top_n_scorelines(matrix: np.ndarray, n: int = 10) -> list[dict]:
    flat = [(f"{i}-{j}", float(matrix[i, j])) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])]
    flat.sort(key=lambda x: -x[1])
    return [{"score": s, "probability": round(p, 6)} for s, p in flat[:n]]


def scoreline_entropy(matrix: np.ndarray) -> float:
    p = matrix.flatten()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))
