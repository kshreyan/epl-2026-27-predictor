"""Rolling-origin backtest for UEFA Nations League, real 2024-25 data.

Not `backtest.py --league nations_league`: that module's rolling-
origin design validates across seven real domestic seasons
(VALIDATION_SEASONS, a module-level constant), refitting every ~10
matches within each. Nations League has exactly one prior real cycle
(2024-25, 167 scored matches after excluding one real abandoned
fixture -- see collect_nations_league_historical.py) to validate on at
all, so there is no earlier season to warm up on before a validation
window begins. This script instead walks forward within that single
season: refits Dixon-Coles before each real match round (a round is
~26 matches across all UEFA groups, all played within 2-3 real days of
each other) using only real matches strictly before it, then scores
that round. Round 1 (the season's first 26 matches) has no real prior
Nations League data to fit on at all and is excluded from scoring, not
predicted from nothing.

This is a genuinely thin backtest -- ~140 scored matches, versus a
domestic league's 2,000+ -- and every report this produces must say so
plainly. Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused
unchanged from config/model_config.yaml (the domestic, club-football-
tuned values): there is nowhere near enough real Nations League data
to independently tune them without just overfitting to noise.

Run: python -m src.evaluation.backtest_nations_league
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row, rps, team_rolling_goal_avgs  # noqa: E402
from src.models.baselines import elo_only_probabilities, simple_poisson_baseline  # noqa: E402
from src.models.elo_model import run_elo  # noqa: E402
from src.models.scoreline_models import fit_dixon_coles_model, outcome_probabilities, score_matrix  # noqa: E402

LEAGUE_ID = "nations_league"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "nations_league_historical_matches.csv"
OUT_MATCH_RESULTS = REPO_ROOT / "data" / "outputs" / "nations_league_backtest_match_results.csv"
OUT_MODEL_COMPARISON = REPO_ROOT / "data" / "outputs" / "nations_league_backtest_model_comparison.csv"
OUT_REPORT = REPO_ROOT / "reports" / "nations_league_model_selection_report.md"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"

ROUND_SIZE = 26  # 2024-25's real group-stage round size (all UEFA groups play once per round)

# Real incident this constant fixes: a flat 1500-for-everyone Elo seed,
# updated from only ~3 real matches per team (167 matches / 54 teams),
# does not converge to sane relative strength -- confirmed directly:
# Switzerland (a real League A side that had a genuinely bad 2024-25
# cycle -- lost to Denmark, Spain twice, Serbia) ended up rated BELOW
# San Marino. The real 2024-25 League A/B/C/D tier each team was
# ALREADY placed in before that cycle even started (UEFA's own,
# real, performance-history-based tiering -- not fabricated, and
# known before any 2024-25 match, so using it as a seed here is not a
# leak) is a genuine, available strength signal this was ignoring
# completely. Gaps between tiers are a simplifying assumption, NOT
# independently validated against real data (there isn't enough of it
# to validate a tier-gap size on top of everything else) -- every
# report built from this must say so.
TIER_RATING_OFFSET = {"A": 150.0, "B": 50.0, "C": -50.0, "D": -150.0}


def team_tier_seed_ratings(matches_with_group: pd.DataFrame) -> dict[str, float]:
    """team -> 1500 + TIER_RATING_OFFSET[tier], from each team's real
    group-stage `group` column (e.g. "Group B1" -> tier "B") -- the
    tier it was placed in BEFORE this season's matches, not derived
    from them. Knockout-round rows (group="") are skipped; every team
    that plays a knockout match already played group-stage matches
    with a real group label."""
    grouped = matches_with_group[matches_with_group["group"].notna() & (matches_with_group["group"] != "")]
    tiers = grouped["group"].str.extract(r"Group ([A-D])")[0]
    seed: dict[str, float] = {}
    for home, away, tier in zip(grouped["home_team"], grouped["away_team"], tiers):
        seed[home] = 1500.0 + TIER_RATING_OFFSET[tier]
        seed[away] = 1500.0 + TIER_RATING_OFFSET[tier]
    return seed

with open(MODEL_CONFIG_PATH) as _f:
    _MODEL_CFG = yaml.safe_load(_f)
HALF_LIFE_DAYS = _MODEL_CFG["dixon_coles"]["time_decay_half_life_days"]
L2_REG = _MODEL_CFG["dixon_coles"].get("l2_reg", 0.03)
ELO_K_FACTOR = _MODEL_CFG["elo"]["k_factor"]
ELO_HOME_ADVANTAGE = _MODEL_CFG["elo"]["home_advantage_elo_points"]


def main() -> None:
    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    teams = sorted(set(df["home_team"]) | set(df["away_team"]))

    tier_seed = team_tier_seed_ratings(df)
    elo_run = run_elo(df, seed_ratings=tier_seed, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    elo_pre = elo_run.history[["home_team", "away_team", "date", "home_elo_pre", "away_elo_pre"]]

    n_rounds = int(np.ceil(len(df) / ROUND_SIZE))
    rows = []
    for round_idx in range(1, n_rounds):  # round 0 (matches[:ROUND_SIZE]) has no prior data -- not scored
        start, end = round_idx * ROUND_SIZE, min((round_idx + 1) * ROUND_SIZE, len(df))
        history_before = df.iloc[:start]
        round_matches = df.iloc[start:end]
        if history_before.empty or round_matches.empty:
            continue

        as_of_date = round_matches["date"].min()
        dc_fit = fit_dixon_coles_model(history_before, teams, as_of_date, half_life_days=HALF_LIFE_DAYS, l2_reg=L2_REG)
        league_avg_goals = float(pd.concat([history_before["home_goals"], history_before["away_goals"]]).mean())

        for _, m in round_matches.iterrows():
            home, away = m["home_team"], m["away_team"]
            actual = m["result"]

            lam = float(np.exp(dc_fit.home_advantage + dc_fit.attack[dc_fit.team_index[home]] - dc_fit.defense[dc_fit.team_index[away]]))
            mu = float(np.exp(dc_fit.attack[dc_fit.team_index[away]] - dc_fit.defense[dc_fit.team_index[home]]))
            matrix = score_matrix(lam, mu, dc_fit.rho)
            dc_h, dc_d, dc_a = outcome_probabilities(matrix)

            elo_row = elo_pre[(elo_pre["home_team"] == home) & (elo_pre["away_team"] == away) & (elo_pre["date"] == m["date"])]
            r_home, r_away = float(elo_row["home_elo_pre"].iloc[0]), float(elo_row["away_elo_pre"].iloc[0])
            elo_h, elo_d, elo_a = elo_only_probabilities(r_home, r_away, ELO_HOME_ADVANTAGE)

            h_gf, h_ga = team_rolling_goal_avgs(history_before, home)
            a_gf, a_ga = team_rolling_goal_avgs(history_before, away)
            sp_lam, sp_mu = simple_poisson_baseline(h_gf, h_ga, a_gf, a_ga, league_avg_goals)
            sp_matrix = score_matrix(sp_lam, sp_mu, rho=0.0)
            sp_h, sp_d, sp_a = outcome_probabilities(sp_matrix)

            dc_probs = {"home_win": dc_h, "draw": dc_d, "away_win": dc_a}
            elo_probs = {"home_win": elo_h, "draw": elo_d, "away_win": elo_a}
            sp_probs = {"home_win": sp_h, "draw": sp_d, "away_win": sp_a}

            rows.append({
                "date": m["date"].strftime("%Y-%m-%d"), "home_team": home, "away_team": away,
                "actual_home_goals": int(m["home_goals"]), "actual_away_goals": int(m["away_goals"]), "actual_result": actual,
                "dc_home_win": dc_h, "dc_draw": dc_d, "dc_away_win": dc_a,
                "dc_lambda": lam, "dc_mu": mu, "dc_rho": dc_fit.rho,
                "elo_home_win": elo_h, "elo_draw": elo_d, "elo_away_win": elo_a,
                "simplepoisson_home_win": sp_h, "simplepoisson_draw": sp_d, "simplepoisson_away_win": sp_a,
                "dc_log_loss": log_loss_row(dc_probs, actual), "dc_brier": brier_row(dc_probs, actual), "dc_rps": rps(dc_probs, actual),
                "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                "simplepoisson_log_loss": log_loss_row(sp_probs, actual), "simplepoisson_brier": brier_row(sp_probs, actual),
                "simplepoisson_rps": rps(sp_probs, actual),
            })

    match_results = pd.DataFrame(rows)
    OUT_MATCH_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    match_results.to_csv(OUT_MATCH_RESULTS, index=False)
    print(f"Wrote {len(match_results)} real scored backtest matches to {OUT_MATCH_RESULTS}")

    comparison_rows = []
    for model in ["dc", "elo", "simplepoisson"]:
        comparison_rows.append({
            "model": {"dc": "Dixon-Coles (main model)", "elo": "Elo-only baseline", "simplepoisson": "Simple Poisson baseline"}[model],
            "n_matches": len(match_results),
            "log_loss": match_results[f"{model}_log_loss"].mean(),
            "brier_score": match_results[f"{model}_brier"].mean(),
            "ranked_probability_score": match_results[f"{model}_rps"].mean(),
        })
    comparison = pd.DataFrame(comparison_rows).sort_values("log_loss")
    comparison.to_csv(OUT_MODEL_COMPARISON, index=False)
    print(f"Wrote model comparison to {OUT_MODEL_COMPARISON}")

    best = comparison.iloc[0]
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REPORT, "w") as f:
        f.write("# UEFA Nations League Model Selection Report (Phase 1)\n\n")
        f.write(
            "**Genuinely thin backtest -- read with real caution.** Nations League has only one prior "
            f"real cycle (2024-25) to validate on, versus 2,000+ real matches for each domestic league "
            f"in this project. This backtest scores {len(match_results)} real matches (every round after "
            "the season's first, which has no real prior Nations League data to fit on) -- roughly 5% of "
            "a domestic league's sample. Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused "
            "unchanged from the domestic config (config/model_config.yaml); there is not enough real "
            "Nations League data to independently tune them without overfitting to noise.\n\n"
        )
        f.write("## Model comparison (lower log loss / Brier / RPS is better)\n\n")
        f.write(comparison.to_markdown(index=False))
        f.write(f"\n\n## Selected model\n\n**{best['model']}** has the lowest backtest log loss "
                f"({best['log_loss']:.4f}) and is used as the primary model for 2026-27 international-break "
                f"predictions.\n\n")
        f.write(
            "## Limitations\n\n"
            "- Sample size (see above) is far too small for isotonic calibration (this project's own "
            "500-match minimum) -- raw model probabilities are used uncalibrated.\n"
            "- No historical market-odds source exists for this competition (no football-data.co.uk "
            "coverage) -- no model+market blend backtest could be run; real current market odds (The "
            "Odds API) are shown alongside predictions for comparison only, not blended in.\n"
            "- No promoted-team adjustment: every 2026-27 participant already has real matches in the "
            "2024-25 historical data (confirmed directly), so none is needed.\n"
            "- Time-decay half-life (269 days) and all other hyperparameters are the domestic, club-"
            "football-tuned defaults, not independently validated for international football's much "
            "sparser real match calendar.\n"
            f"- Elo is seeded from each team's real pre-season League A/B/C/D tier (not flat 1500 for "
            f"everyone -- see TIER_RATING_OFFSET), a real signal a flat seed was found to get badly "
            f"wrong with this little data (a real League A side, Switzerland, rated below San Marino). "
            f"The {TIER_RATING_OFFSET['A']-TIER_RATING_OFFSET['D']:.0f}-point top-to-bottom tier gap "
            f"is a simplifying assumption, not independently validated against real data.\n"
        )
    print(f"Wrote model selection report to {OUT_REPORT}")


if __name__ == "__main__":
    main()
