"""Season-level calibration backtest for the preseason Monte Carlo simulation.

Match-level calibration (see backtest.py, ECE 0.0114) says nothing about
whether SEASON-level aggregates -- title, top-4, relegation probabilities
-- are calibrated. A model can nail every match's 1X2 probabilities and
still be badly overconfident about who wins the league, because season
outcomes compound 38 correlated match outcomes through a table.

For each of the 7 real historical seasons already used in the match-level
backtest (2019-20 through 2025-26), this script:

1. Fits Dixon-Coles + the promoted-team adjustment using ONLY match data
   strictly before that season's first ball -- the same preseason-only
   information a forecaster actually had at the time. No mid-season
   refitting (this checks the PRESEASON forecast, not a weekly-updated
   one).
2. Runs the exact same parameter-uncertainty Monte Carlo used for the
   real 2026-27 forecast (see simulate_full_season.TeamStrengthUncertainty)
   over that season's real 380 fixtures.
3. Compares the resulting title/top-4/relegation probabilities against
   what actually happened that season.

Run: python -m src.evaluation.season_calibration_backtest
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.dynamic_team_strength_state_space import compute_team_strength_state  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    _season_table,
    compute_promoted_team_history,
    summarize_promoted_team_baseline,
)
from src.simulation.simulate_full_season import run_monte_carlo  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
SIM_CONFIG_PATH = REPO_ROOT / "config" / "simulation_config.yaml"
OUT_DETAIL = REPO_ROOT / "data" / "outputs" / "epl_season_calibration_backtest.csv"
OUT_SUMMARY = REPO_ROOT / "data" / "outputs" / "epl_season_calibration_summary.csv"

VALIDATION_SEASONS = [
    "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
]
RELEGATION_ZONE_SIZE = 3
TOP4_SIZE = 4

N_SIMULATIONS = 250_000  # same scale as the real production preseason run


def brier(preds: np.ndarray, actuals: np.ndarray) -> float:
    return float(np.mean((preds - actuals) ** 2))


def log_loss(preds: np.ndarray, actuals: np.ndarray, eps: float = 1e-6) -> float:
    p = np.clip(preds, eps, 1 - eps)
    return float(-np.mean(actuals * np.log(p) + (1 - actuals) * np.log(1 - p)))


def main() -> None:
    with open(MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)
    with open(SIM_CONFIG_PATH) as f:
        sim_cfg = yaml.safe_load(f)

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)

    all_seasons_in_order = list(dict.fromkeys(df.sort_values("date")["season"]))
    teams_by_season = {
        s: set(df[df["season"] == s]["home_team"]) | set(df[df["season"] == s]["away_team"])
        for s in all_seasons_in_order
    }

    detail_rows = []

    for i, season in enumerate(VALIDATION_SEASONS):
        season_matches = df[df["season"] == season].sort_values("date").reset_index(drop=True)
        if season_matches.empty:
            print(f"skipping {season}: no data")
            continue

        season_idx = all_seasons_in_order.index(season)
        prev_season = all_seasons_in_order[season_idx - 1] if season_idx > 0 else None
        teams_this_season = sorted(teams_by_season[season])
        promoted_this_season = sorted(
            teams_by_season[season] - teams_by_season[prev_season] if prev_season else set()
        )

        as_of_date = season_matches["date"].iloc[0]
        history_before_season = df[df["date"] < as_of_date]

        promo_history = compute_promoted_team_history(history_before_season)
        promo_summary = summarize_promoted_team_baseline(promo_history)
        shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
        shortfall_std = promo_summary["std_points_below_league_avg"] or 12.5
        dc_attack_offset = shortfall / 100.0
        dc_defense_offset = shortfall / 100.0
        promoted_se = shortfall_std / 100.0

        hist_teams = sorted(set(history_before_season["home_team"]) | set(history_before_season["away_team"]))
        universe = sorted(set(hist_teams) | set(teams_this_season))

        strength_df, fit = compute_team_strength_state(
            history_before_season, universe, as_of_date=as_of_date,
            promoted_teams=promoted_this_season,
            promoted_attack_offset=dc_attack_offset, promoted_defense_offset=dc_defense_offset,
            half_life_days=model_cfg["dixon_coles"]["time_decay_half_life_days"],
            shrinkage_to_league_prior=model_cfg["dynamic_team_strength"]["shrinkage_to_league_prior"],
            promoted_extra_shrinkage=model_cfg["dynamic_team_strength"]["promoted_team_extra_shrinkage"],
            l2_reg=model_cfg["dixon_coles"].get("l2_reg"),
        )

        fixtures_df = season_matches[["home_team", "away_team"]].copy()

        seed = sim_cfg["random_seed"] + i
        expected_table, _ = run_monte_carlo(
            fixtures_df, fit, teams_this_season, N_SIMULATIONS, seed, sim_cfg, promoted_se,
        )

        actual_table = _season_table(season_matches)
        n_teams = len(actual_table)
        actual_table["actual_champion"] = actual_table["final_rank"] == 1
        actual_table["actual_top4"] = actual_table["final_rank"] <= TOP4_SIZE
        actual_table["actual_relegated"] = actual_table["final_rank"] > n_teams - RELEGATION_ZONE_SIZE

        merged = expected_table.merge(actual_table[["team", "final_rank", "actual_champion", "actual_top4", "actual_relegated"]], on="team")
        merged["season"] = season
        merged["is_promoted_team"] = merged["team"].isin(promoted_this_season)
        merged["promoted_se_used"] = promoted_se
        merged["n_prior_promotion_events"] = promo_summary["n_promotion_events"]

        detail_rows.append(merged[[
            "season", "team", "final_rank", "is_promoted_team",
            "title_probability", "actual_champion",
            "top_4_probability", "actual_top4",
            "relegation_probability", "actual_relegated",
            "promoted_se_used", "n_prior_promotion_events",
        ]])

        champ_row = actual_table[actual_table["actual_champion"]].iloc[0]
        predicted_champ_prob = merged.loc[merged["team"] == champ_row["team"], "title_probability"].iloc[0]
        print(f"{season}: actual champion {champ_row['team']} (predicted title prob {predicted_champ_prob:.3f}); "
              f"n_prior_promotion_events={promo_summary['n_promotion_events']}, promoted_se={promoted_se:.3f}")

    detail = pd.concat(detail_rows, ignore_index=True)
    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUT_DETAIL, index=False)

    summary_rows = []
    for label, prob_col, actual_col in [
        ("title", "title_probability", "actual_champion"),
        ("top_4", "top_4_probability", "actual_top4"),
        ("relegation", "relegation_probability", "actual_relegated"),
    ]:
        preds = detail[prob_col].to_numpy(dtype=float)
        actuals = detail[actual_col].to_numpy(dtype=float)
        summary_rows.append({
            "target": label,
            "n_observations": len(detail),
            "n_positive": int(actuals.sum()),
            "brier_score": round(brier(preds, actuals), 5),
            "log_loss": round(log_loss(preds, actuals), 5),
            "mean_predicted_probability": round(float(preds.mean()), 5),
            "empirical_base_rate": round(float(actuals.mean()), 5),
        })

    n_seasons = detail["season"].nunique()
    champion_hit_rate = np.mean([
        (detail[(detail["season"] == s) & (detail["actual_champion"])]["title_probability"].iloc[0]
         >= detail[detail["season"] == s]["title_probability"].max() - 1e-9)
        for s in detail["season"].unique()
    ])
    promoted = detail[detail["is_promoted_team"]]
    promoted_relegation_predicted_mean = promoted["relegation_probability"].mean()
    promoted_relegation_actual_rate = promoted["actual_relegated"].mean()

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, index=False)

    print()
    print(summary.to_string(index=False))
    print()
    print(f"n_seasons={n_seasons}, model's top title-probability team was the actual champion in "
          f"{champion_hit_rate:.0%} of seasons")
    print(f"promoted teams: mean predicted relegation probability {promoted_relegation_predicted_mean:.3f} "
          f"vs actual relegation rate {promoted_relegation_actual_rate:.3f} "
          f"(n={len(promoted)} promoted-team-seasons)")
    print(f"generated_at={now_utc_iso()}")


if __name__ == "__main__":
    main()
