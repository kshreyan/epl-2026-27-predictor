"""Full 2026-27 season Monte Carlo simulation (250,000 runs, model-only).

Phase-1 design: since today (2026-08-18) is before kickoff, every one
of the 380 real fixtures is still to be played, so this is a pure
preseason simulation -- team strength is held fixed at the preseason
Dixon-Coles state for the whole season (the weekly-update engine, a
later phase, is what re-simulates with updated strength after each
real matchweek; simulating with in-run dynamic strength updates across
250k paths x 380 matches is a materially larger project and is
documented as a limitation below, not attempted here).

For each of the 380 real fixtures, we precompute its Dixon-Coles
scoreline probability matrix once, then draw `n_simulations` scorelines
from that fixed distribution via inverse-CDF sampling (vectorized).
League tables are built for every simulated season using real
Premier League points/goal-difference/goals-scored tie-break order;
head-to-head is NOT implemented (see limitation note) -- any remaining
tie is broken by a fixed, documented, deterministic rule (alphabetical
team order), never left ambiguous or randomly reshuffled per run.

Runs in memory-safe batches (default 25,000 sims/batch) rather than
allocating one (250000, 380) array, which would be very large.

Run: python -m src.simulation.simulate_full_season
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.elo_model import compute_promoted_team_elo_offset  # noqa: E402
from src.models.promoted_team_adjustment import compute_promoted_team_history, summarize_promoted_team_baseline  # noqa: E402
from src.models.dynamic_team_strength_state_space import compute_team_strength_state  # noqa: E402
from src.models.scoreline_models import match_lambdas, score_matrix  # noqa: E402
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
SIM_CONFIG_PATH = REPO_ROOT / "config" / "simulation_config.yaml"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"

OUT_DIR = REPO_ROOT / "data" / "outputs"
PROMOTED_TEAMS = ["Coventry City", "Ipswich Town", "Hull City"]
MAX_GOALS = 8
BATCH_SIZE = 25000


def build_score_distributions(fixtures_df: pd.DataFrame, fit) -> list[np.ndarray]:
    """One flattened, cumulative-sum probability vector per fixture (length
    (MAX_GOALS+1)^2), for fast inverse-CDF sampling."""
    cdfs = []
    for _, fx in fixtures_df.iterrows():
        lam, mu = match_lambdas(fit, fx["home_team"], fx["away_team"])
        matrix = score_matrix(lam, mu, fit.rho, max_goals=MAX_GOALS)
        flat = matrix.flatten()
        cdfs.append(np.cumsum(flat))
    return cdfs


def simulate_batch(cdfs: list[np.ndarray], n_sims: int, rng: np.random.Generator, grid_size: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns (home_goals, away_goals), each shape (n_sims, n_fixtures)."""
    n_fixtures = len(cdfs)
    home_goals = np.zeros((n_sims, n_fixtures), dtype=np.int16)
    away_goals = np.zeros((n_sims, n_fixtures), dtype=np.int16)
    for m, cdf in enumerate(cdfs):
        u = rng.random(n_sims)
        flat_idx = np.searchsorted(cdf, u, side="right")
        flat_idx = np.clip(flat_idx, 0, grid_size * grid_size - 1)
        home_goals[:, m] = flat_idx // grid_size
        away_goals[:, m] = flat_idx % grid_size
    return home_goals, away_goals


def build_tables(
    home_goals: np.ndarray, away_goals: np.ndarray, home_idx: np.ndarray, away_idx: np.ndarray, n_teams: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized league-table build across all sims in a batch.
    Returns (points, goal_diff, goals_for), each shape (n_sims, n_teams)."""
    n_sims, n_fixtures = home_goals.shape
    points = np.zeros((n_sims, n_teams), dtype=np.int32)
    goals_for = np.zeros((n_sims, n_teams), dtype=np.int32)
    goals_against = np.zeros((n_sims, n_teams), dtype=np.int32)

    home_pts = np.where(home_goals > away_goals, 3, np.where(home_goals == away_goals, 1, 0))
    away_pts = np.where(away_goals > home_goals, 3, np.where(home_goals == away_goals, 1, 0))

    for m in range(n_fixtures):
        h, a = home_idx[m], away_idx[m]
        points[:, h] += home_pts[:, m]
        points[:, a] += away_pts[:, m]
        goals_for[:, h] += home_goals[:, m]
        goals_for[:, a] += away_goals[:, m]
        goals_against[:, h] += away_goals[:, m]
        goals_against[:, a] += home_goals[:, m]

    goal_diff = goals_for - goals_against
    return points, goal_diff, goals_for


def weighted_position_percentile(pos_probs: np.ndarray, q: float) -> int:
    """Smallest 1-indexed position whose cumulative probability reaches q."""
    cumsum = np.cumsum(pos_probs)
    idx = int(np.searchsorted(cumsum, q, side="left"))
    return min(idx + 1, len(pos_probs))


def rank_teams(points: np.ndarray, goal_diff: np.ndarray, goals_for: np.ndarray, teams: list[str]) -> np.ndarray:
    """Returns positions (1=top), shape (n_sims, n_teams), applying the
    points -> goal_difference -> goals_for -> alphabetical tie-break order."""
    n_sims, n_teams = points.shape
    alpha_rank = np.argsort(np.argsort(teams))  # 0 = alphabetically first
    alpha_bonus = (n_teams - alpha_rank)  # earlier alphabetically -> larger bonus

    # Each subordinate term's multiplier must exceed the *maximum possible*
    # value of everything below it, or a large goals-for/goal-diff swing in
    # one simulated season could bleed into the next tie-break tier and
    # corrupt a comparison between different points totals. A single team
    # cannot exceed ~150 goals for/against or +-150 goal difference in a
    # 38-match season, and alpha_bonus is bounded by n_teams (<=20), so:
    composite = (
        points.astype(np.int64) * 10_000_000_000        # dominates goal_diff term (max ~1.15e9) by 10x+
        + (goal_diff.astype(np.int64) + 1000) * 1_000_000  # dominates goals_for term (max ~150,020) by 6x+
        + goals_for.astype(np.int64) * 1_000                # dominates alpha_bonus (max 20) by 50x+
        + alpha_bonus[np.newaxis, :]
    )
    order = np.argsort(-composite, axis=1)  # best team first, per sim
    positions = np.empty_like(order)
    row_idx = np.arange(n_sims)[:, None]
    ranks = np.tile(np.arange(1, n_teams + 1), (n_sims, 1))
    positions[row_idx, order] = ranks
    return positions


def run_monte_carlo(
    fixtures_df: pd.DataFrame,
    fit,
    teams_2627: list[str],
    n_simulations: int,
    seed: int,
    sim_cfg: dict,
    initial_points: dict[str, int] | None = None,
    initial_goals_for: dict[str, int] | None = None,
    initial_goals_against: dict[str, int] | None = None,
    initial_wins: dict[str, int] | None = None,
    initial_draws: dict[str, int] | None = None,
    initial_losses: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Runs the batched Monte Carlo simulation over `fixtures_df` (which
    may be all 380 fixtures for a preseason run, or only the *remaining*
    fixtures for a mid-season weekly-update run) and returns
    (expected_table, position_distribution).

    `initial_*` dicts let a caller lock in real, already-completed
    results as a fixed baseline that every simulated path starts from
    -- this is what makes a weekly-update run "simulate the rest of the
    season given what has actually happened so far" rather than
    re-simulating already-known results.
    """
    n_teams = len(teams_2627)
    team_pos_idx = {t: i for i, t in enumerate(teams_2627)}
    home_idx = fixtures_df["home_team"].map(team_pos_idx).to_numpy()
    away_idx = fixtures_df["away_team"].map(team_pos_idx).to_numpy()

    def _init_array(d: dict | None) -> np.ndarray:
        arr = np.zeros(n_teams, dtype=np.int64)
        if d:
            for team, v in d.items():
                arr[team_pos_idx[team]] = v
        return arr

    base_points = _init_array(initial_points)
    base_gf = _init_array(initial_goals_for)
    base_ga = _init_array(initial_goals_against)
    base_wins = _init_array(initial_wins)
    base_draws = _init_array(initial_draws)
    base_losses = _init_array(initial_losses)

    cdfs = build_score_distributions(fixtures_df, fit)
    grid_size = MAX_GOALS + 1

    remaining = n_simulations
    rng = np.random.default_rng(seed)

    position_counts = np.zeros((n_teams, n_teams), dtype=np.int64)
    points_samples = [[] for _ in range(n_teams)]
    gf_samples = [[] for _ in range(n_teams)]
    ga_samples = [[] for _ in range(n_teams)]
    win_samples = [[] for _ in range(n_teams)]
    draw_samples = [[] for _ in range(n_teams)]
    loss_samples = [[] for _ in range(n_teams)]

    n_run = 0
    while remaining > 0:
        batch = min(BATCH_SIZE, remaining)
        if len(cdfs) > 0:
            hg, ag = simulate_batch(cdfs, batch, rng, grid_size)
            points, goal_diff, goals_for = build_tables(hg, ag, home_idx, away_idx, n_teams)
            goals_against = goals_for - goal_diff
        else:
            # No remaining fixtures (season fully complete) -- every sim is
            # just the locked baseline, with no scorelines to draw.
            points = np.zeros((batch, n_teams), dtype=np.int64)
            goals_for = np.zeros((batch, n_teams), dtype=np.int64)
            goals_against = np.zeros((batch, n_teams), dtype=np.int64)
            hg = ag = np.zeros((batch, 0), dtype=np.int64)

        points = points + base_points[np.newaxis, :]
        goals_for = goals_for + base_gf[np.newaxis, :]
        goals_against = goals_against + base_ga[np.newaxis, :]
        goal_diff = goals_for - goals_against
        positions = rank_teams(points, goal_diff, goals_for, teams_2627)

        for t in range(n_teams):
            for p in range(1, n_teams + 1):
                position_counts[t, p - 1] += int((positions[:, t] == p).sum())
            points_samples[t].append(points[:, t])
            gf_samples[t].append(goals_for[:, t])
            ga_samples[t].append(goals_against[:, t])

        if len(cdfs) > 0:
            for t in range(n_teams):
                home_mask = home_idx == t
                away_mask = away_idx == t
                wins = (hg[:, home_mask] > ag[:, home_mask]).sum(axis=1) + (ag[:, away_mask] > hg[:, away_mask]).sum(axis=1)
                draws = (hg[:, home_mask] == ag[:, home_mask]).sum(axis=1) + (ag[:, away_mask] == hg[:, away_mask]).sum(axis=1)
                losses = (hg[:, home_mask] < ag[:, home_mask]).sum(axis=1) + (ag[:, away_mask] < hg[:, away_mask]).sum(axis=1)
                win_samples[t].append(wins + base_wins[t])
                draw_samples[t].append(draws + base_draws[t])
                loss_samples[t].append(losses + base_losses[t])
        else:
            for t in range(n_teams):
                win_samples[t].append(np.full(batch, base_wins[t]))
                draw_samples[t].append(np.full(batch, base_draws[t]))
                loss_samples[t].append(np.full(batch, base_losses[t]))

        n_run += batch
        remaining -= batch
        print(f"  simulated {n_run}/{n_simulations}")

    generated_at = now_utc_iso()
    expected_rows, position_rows = [], []

    for t, team in enumerate(teams_2627):
        pts = np.concatenate(points_samples[t])
        gf = np.concatenate(gf_samples[t])
        ga = np.concatenate(ga_samples[t])
        wins = np.concatenate(win_samples[t])
        draws = np.concatenate(draw_samples[t])
        losses = np.concatenate(loss_samples[t])
        pos_probs = position_counts[t] / n_simulations
        positions_1indexed = np.arange(1, n_teams + 1)
        median_position = int(np.searchsorted(np.cumsum(pos_probs), 0.5) + 1)

        expected_rows.append({
            "team": team,
            "expected_position": round(float(np.dot(pos_probs, positions_1indexed)), 3),
            "median_position": median_position,
            "position_5th_percentile": weighted_position_percentile(pos_probs, 0.05),
            "position_25th_percentile": weighted_position_percentile(pos_probs, 0.25),
            "position_75th_percentile": weighted_position_percentile(pos_probs, 0.75),
            "position_95th_percentile": weighted_position_percentile(pos_probs, 0.95),
            "expected_points": round(float(pts.mean()), 2),
            "points_5th_percentile": float(np.percentile(pts, 5)),
            "points_25th_percentile": float(np.percentile(pts, 25)),
            "median_points": float(np.percentile(pts, 50)),
            "points_75th_percentile": float(np.percentile(pts, 75)),
            "points_95th_percentile": float(np.percentile(pts, 95)),
            "expected_wins": round(float(wins.mean()), 2),
            "expected_draws": round(float(draws.mean()), 2),
            "expected_losses": round(float(losses.mean()), 2),
            "expected_goals_for": round(float(gf.mean()), 2),
            "expected_goals_against": round(float(ga.mean()), 2),
            "expected_goal_difference": round(float((gf - ga).mean()), 2),
            "title_probability": round(float(pos_probs[0]), 5),
            "top_4_probability": round(float(pos_probs[:4].sum()), 5),
            "top_5_probability": round(float(pos_probs[:5].sum()), 5),
            "top_half_probability": round(float(pos_probs[:sim_cfg["top_half_size"]].sum()), 5),
            "relegation_probability": round(float(pos_probs[-sim_cfg["relegation_zone_size"]:].sum()), 5),
            "most_likely_finish": int(np.argmax(pos_probs) + 1),
            "model_version": MODEL_VERSION,
            "generated_at": generated_at,
        })

        pos_row = {"team": team}
        for p in range(1, n_teams + 1):
            pos_row[f"finish_{p}_probability"] = round(float(pos_probs[p - 1]), 5)
        position_rows.append(pos_row)

    expected_table = pd.DataFrame(expected_rows).sort_values("expected_position").reset_index(drop=True)
    position_dist = pd.DataFrame(position_rows)
    return expected_table, position_dist


def main() -> None:
    with open(SIM_CONFIG_PATH) as f:
        sim_cfg = yaml.safe_load(f)
    with open(MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)

    n_simulations = sim_cfg["n_simulations"]
    seed = sim_cfg["random_seed"]

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    promoted_elo_offset, n_events = compute_promoted_team_elo_offset(df_clean)
    promo_history = compute_promoted_team_history(df_clean)
    promo_summary = summarize_promoted_team_baseline(promo_history)
    # Convert the empirical points-shortfall into an approximate Dixon-Coles
    # attack/defense offset: EPL goal supply is roughly linear in points
    # over a season, so we split the shortfall between attack (scores
    # fewer) and defense (concedes more) in a simple, documented way.
    points_shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
    # Both offsets share the sign of points_shortfall (negative for a
    # below-average team): defense[i] is SUBTRACTED in the Dixon-Coles
    # exponent, so a lower defense value means concedes MORE -- the same
    # (negative) direction as attack makes a promoted team weaker on both
    # ends, not stronger on one.
    dc_attack_offset = points_shortfall / 100.0
    dc_defense_offset = points_shortfall / 100.0

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    strength_df, fit = compute_team_strength_state(
        df_clean, universe, as_of_date=as_of_date,
        promoted_teams=PROMOTED_TEAMS,
        promoted_attack_offset=dc_attack_offset, promoted_defense_offset=dc_defense_offset,
        half_life_days=model_cfg["dixon_coles"]["time_decay_half_life_days"],
        shrinkage_to_league_prior=model_cfg["dynamic_team_strength"]["shrinkage_to_league_prior"],
        promoted_extra_shrinkage=model_cfg["dynamic_team_strength"]["promoted_team_extra_shrinkage"],
        l2_reg=model_cfg["dixon_coles"].get("l2_reg"),
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    strength_df.to_csv(OUT_DIR / "epl_2026_27_dynamic_team_strength.csv", index=False)
    print(f"Wrote preseason dynamic team strength for {len(strength_df)} teams")

    fixtures_df = pd.read_csv(FIXTURES_PATH)
    fixtures_df = fixtures_df.sort_values(["matchweek", "kickoff_utc"]).reset_index(drop=True)
    teams_2627 = EPL_2026_27_CLUBS

    expected_table, position_dist = run_monte_carlo(fixtures_df, fit, teams_2627, n_simulations, seed, sim_cfg)
    generated_at = now_utc_iso()

    expected_table.to_csv(OUT_DIR / "epl_2026_27_expected_table.csv", index=False)
    expected_table.to_csv(OUT_DIR / "epl_2026_27_table_probabilities.csv", index=False)
    position_dist.to_csv(OUT_DIR / "epl_2026_27_position_distribution.csv", index=False)

    title_race = expected_table[["team", "title_probability", "expected_points", "median_points"]].sort_values(
        "title_probability", ascending=False
    )
    title_race.to_csv(OUT_DIR / "epl_2026_27_title_race.csv", index=False)

    top4 = expected_table[["team", "top_4_probability", "expected_points", "expected_position"]].sort_values(
        "top_4_probability", ascending=False
    )
    top4.to_csv(OUT_DIR / "epl_2026_27_top4_probabilities.csv", index=False)

    relegation = expected_table[["team", "relegation_probability", "expected_points", "expected_position"]].sort_values(
        "relegation_probability", ascending=False
    )
    relegation.to_csv(OUT_DIR / "epl_2026_27_relegation_probabilities.csv", index=False)

    full_sim_summary = pd.DataFrame([{
        "n_simulations": n_simulations,
        "n_fixtures_per_simulation": len(fixtures_df),
        "season": "2026-27",
        "simulation_mode": "preseason_static_strength",
        "tie_break_order": "points, goal_difference, goals_for, alphabetical_fallback (no head-to-head)",
        "random_seed": seed,
        "model_version": MODEL_VERSION,
        "generated_at": generated_at,
    }])
    full_sim_summary.to_csv(OUT_DIR / "epl_2026_27_full_season_simulation.csv", index=False)

    print(f"Wrote season simulation outputs ({n_simulations} sims) to {OUT_DIR}")

    meta = make_run_metadata(prefix="simulation", season="2026-27")
    log_experiment(meta, stage="full_season_simulation", notes=f"{n_simulations} sims, promoted_elo_offset={promoted_elo_offset:.1f}")


if __name__ == "__main__":
    main()
