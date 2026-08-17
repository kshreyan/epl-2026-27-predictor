"""Strict time-based rolling-origin backtest on real EPL historical data.

Validates the Dixon-Coles model (the system's core scoreline engine)
against three honest baselines -- Elo-only, previous-season-table, and
a simple (non-Dixon-Coles) Poisson model -- across 7 real seasons
(2019/20-2025/26), refitting roughly every "matchweek" (chunks of 10
chronologically-ordered matches) using only matches strictly before
that chunk. No random splitting, no future data.

Run: python -m src.evaluation.backtest
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.baselines import (  # noqa: E402
    elo_only_probabilities,
    previous_season_table_baseline,
    simple_poisson_baseline,
)
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    compute_promoted_team_history,
    summarize_promoted_team_baseline,
)
from src.models.scoreline_models import (  # noqa: E402
    apply_promoted_team_adjustment,
    fit_dixon_coles_model,
    match_lambdas,
    outcome_probabilities,
    score_matrix,
    top_n_scorelines,
)
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, register_model  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
OUT_MATCH_RESULTS = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
OUT_MODEL_COMPARISON = REPO_ROOT / "data" / "outputs" / "epl_backtest_model_comparison.csv"
OUT_SCORELINE_ACCURACY = REPO_ROOT / "data" / "outputs" / "epl_backtest_scoreline_accuracy.csv"
OUT_BASELINE_RESULTS = REPO_ROOT / "data" / "outputs" / "baseline_model_results.csv"
OUT_SELECTION_REPORT = REPO_ROOT / "reports" / "epl_model_selection_report.md"

VALIDATION_SEASONS = [
    "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
]
CHUNK_SIZE = 10  # ~1 matchweek in a 20-team league

with open(MODEL_CONFIG_PATH) as _f:
    _MODEL_CFG = yaml.safe_load(_f)
HALF_LIFE_DAYS = _MODEL_CFG["dixon_coles"]["time_decay_half_life_days"]
L2_REG = _MODEL_CFG["dixon_coles"].get("l2_reg", 0.03)
ELO_K_FACTOR = _MODEL_CFG["elo"]["k_factor"]
ELO_HOME_ADVANTAGE = _MODEL_CFG["elo"]["home_advantage_elo_points"]

RESULT_ORDER = ["away_win", "draw", "home_win"]  # ordinal scale for RPS


def rps(probs: dict, actual: str) -> float:
    """Ranked Probability Score over the 3 ordered outcome categories."""
    p_cum, a_cum, total = 0.0, 0.0, 0.0
    actual_idx = RESULT_ORDER.index(actual)
    for i, cat in enumerate(RESULT_ORDER):
        p_cum += probs[cat]
        a_cum += 1.0 if i == actual_idx else 0.0
        if i < len(RESULT_ORDER) - 1:
            total += (p_cum - a_cum) ** 2
    return total / (len(RESULT_ORDER) - 1)


def log_loss_row(probs: dict, actual: str) -> float:
    p = max(probs[actual], 1e-12)
    return -np.log(p)


def brier_row(probs: dict, actual: str) -> float:
    return sum((probs[c] - (1.0 if c == actual else 0.0)) ** 2 for c in RESULT_ORDER)


def team_rolling_goal_avgs(matches_before: pd.DataFrame, team: str) -> tuple[float, float]:
    home_rows = matches_before[matches_before["home_team"] == team]
    away_rows = matches_before[matches_before["away_team"] == team]
    gf = pd.concat([home_rows["home_goals"], away_rows["away_goals"]])
    ga = pd.concat([home_rows["away_goals"], away_rows["home_goals"]])
    if len(gf) == 0:
        return 1.35, 1.35
    return float(gf.mean()), float(ga.mean())


def main() -> None:
    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)
    hist_teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    promoted_elo_offset, n_events = compute_promoted_team_elo_offset(df)
    elo_run = run_elo(df, promoted_offset=promoted_elo_offset, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    elo_hist = elo_run.history.copy()
    # NOTE: Series.astype(str) on a datetime64 column and str()/f-string on a
    # scalar Timestamp can format differently (date-only vs date+time) --
    # use an explicit strftime on both sides of this join so the key always
    # matches (this caused a silent 100% lookup-miss bug during development).
    elo_hist["key"] = elo_hist["date"].dt.strftime("%Y-%m-%d") + "_" + elo_hist["home_team"] + "_" + elo_hist["away_team"]
    elo_lookup = elo_hist.set_index("key")[["home_elo_pre", "away_elo_pre"]]

    league_avg_goals_overall = float(pd.concat([df["home_goals"], df["away_goals"]]).mean())

    all_seasons_in_order = list(dict.fromkeys(df.sort_values("date")["season"]))
    teams_by_season = {
        s: set(df[df["season"] == s]["home_team"]) | set(df[df["season"] == s]["away_team"])
        for s in all_seasons_in_order
    }

    match_rows = []
    dc_fit = None

    for season in VALIDATION_SEASONS:
        season_matches = df[df["season"] == season].sort_values("date").reset_index(drop=True)
        if season_matches.empty:
            continue

        # Promoted-team detection is season-membership metadata, known
        # publicly before a ball is kicked -- not match-outcome data -- so
        # using it here is not leakage. The *offset magnitude*, however, is
        # computed only from promotion events in seasons strictly before
        # this validation season (leakage-safe), unlike the single global
        # constant used elsewhere in Phase 1 (see model report limitations).
        season_idx = all_seasons_in_order.index(season)
        prev_season = all_seasons_in_order[season_idx - 1] if season_idx > 0 else None
        promoted_this_season = (
            teams_by_season[season] - teams_by_season[prev_season] if prev_season else set()
        )
        history_before_season = df[df["date"] < season_matches["date"].iloc[0]]
        promo_summary = summarize_promoted_team_baseline(compute_promoted_team_history(history_before_season))
        shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
        season_attack_offset = shortfall / 100.0
        season_defense_offset = shortfall / 100.0

        n_chunks = int(np.ceil(len(season_matches) / CHUNK_SIZE))
        for c in range(n_chunks):
            chunk = season_matches.iloc[c * CHUNK_SIZE:(c + 1) * CHUNK_SIZE]
            if chunk.empty:
                continue
            as_of_date = chunk["date"].iloc[0]
            train_pool = df[df["date"] < as_of_date]
            if train_pool.empty:
                continue

            dc_fit = fit_dixon_coles_model(train_pool, universe, as_of_date, HALF_LIFE_DAYS, warm_start=dc_fit, l2_reg=L2_REG)
            dc_fit_for_predictions = (
                apply_promoted_team_adjustment(dc_fit, list(promoted_this_season), season_attack_offset, season_defense_offset)
                if promoted_this_season else dc_fit
            )

            for _, m in chunk.iterrows():
                home, away = m["home_team"], m["away_team"]
                hg, ag = int(m["home_goals"]), int(m["away_goals"])
                actual = "home_win" if hg > ag else ("draw" if hg == ag else "away_win")

                if home not in dc_fit.team_index or away not in dc_fit.team_index:
                    continue

                lam, mu = match_lambdas(dc_fit_for_predictions, home, away)
                matrix = score_matrix(lam, mu, dc_fit_for_predictions.rho)
                dc_home, dc_draw, dc_away = outcome_probabilities(matrix)
                dc_probs = {"home_win": dc_home, "draw": dc_draw, "away_win": dc_away}
                dc_pred_score = max(
                    ((i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])),
                    key=lambda ij: matrix[ij[0], ij[1]],
                )

                key = f"{m['date'].strftime('%Y-%m-%d')}_{home}_{away}"
                if key in elo_lookup.index:
                    elo_home_pre = elo_lookup.loc[key, "home_elo_pre"]
                    elo_away_pre = elo_lookup.loc[key, "away_elo_pre"]
                    if isinstance(elo_home_pre, pd.Series):
                        elo_home_pre, elo_away_pre = elo_home_pre.iloc[0], elo_away_pre.iloc[0]
                else:
                    continue
                eh, ed, ea = elo_only_probabilities(float(elo_home_pre), float(elo_away_pre), home_advantage=ELO_HOME_ADVANTAGE)
                elo_probs = {"home_win": eh, "draw": ed, "away_win": ea}

                pst_h, pst_d, pst_a = previous_season_table_baseline(train_pool, home, away, season)
                pst_probs = {"home_win": pst_h, "draw": pst_d, "away_win": pst_a}

                h_gf, h_ga = team_rolling_goal_avgs(train_pool, home)
                a_gf, a_ga = team_rolling_goal_avgs(train_pool, away)
                sp_lam, sp_mu = simple_poisson_baseline(h_gf, h_ga, a_gf, a_ga, league_avg_goals_overall)
                sp_matrix = score_matrix(sp_lam, sp_mu, rho=0.0)
                sp_home, sp_draw, sp_away = outcome_probabilities(sp_matrix)
                sp_probs = {"home_win": sp_home, "draw": sp_draw, "away_win": sp_away}

                match_rows.append({
                    "season": season, "date": str(m["date"].date()), "home_team": home, "away_team": away,
                    "actual_home_goals": hg, "actual_away_goals": ag, "actual_result": actual,
                    "dc_home_win": dc_home, "dc_draw": dc_draw, "dc_away_win": dc_away,
                    "dc_predicted_score": f"{dc_pred_score[0]}-{dc_pred_score[1]}",
                    "dc_top10_scorelines_json": json.dumps(top_n_scorelines(matrix, 10)),
                    "elo_home_win": eh, "elo_draw": ed, "elo_away_win": ea,
                    "prevseason_home_win": pst_h, "prevseason_draw": pst_d, "prevseason_away_win": pst_a,
                    "simplepoisson_home_win": sp_home, "simplepoisson_draw": sp_draw, "simplepoisson_away_win": sp_away,
                    "simplepoisson_predicted_score": f"{int(np.argmax(sp_matrix.sum(axis=1)))}-{int(np.argmax(sp_matrix.sum(axis=0)))}",
                    "dc_log_loss": log_loss_row(dc_probs, actual), "dc_brier": brier_row(dc_probs, actual), "dc_rps": rps(dc_probs, actual),
                    "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                    "prevseason_log_loss": log_loss_row(pst_probs, actual), "prevseason_brier": brier_row(pst_probs, actual), "prevseason_rps": rps(pst_probs, actual),
                    "simplepoisson_log_loss": log_loss_row(sp_probs, actual), "simplepoisson_brier": brier_row(sp_probs, actual), "simplepoisson_rps": rps(sp_probs, actual),
                })

    results_df = pd.DataFrame(match_rows)
    OUT_MATCH_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUT_MATCH_RESULTS, index=False)
    print(f"Wrote {len(results_df)} backtest match rows to {OUT_MATCH_RESULTS}")

    model_names = ["dc", "elo", "prevseason", "simplepoisson"]
    display_names = {
        "dc": "Dixon-Coles (main model)", "elo": "Elo-only baseline",
        "prevseason": "Previous-season-table baseline", "simplepoisson": "Simple Poisson baseline",
    }
    comparison_rows = []
    for model in model_names:
        pred_result = results_df[[f"{model}_home_win", f"{model}_draw", f"{model}_away_win"]].idxmax(axis=1)
        pred_result = pred_result.str.replace(f"{model}_", "", regex=False)
        accuracy = (pred_result.values == results_df["actual_result"].values).mean()
        favorite_mask = results_df[f"{model}_home_win"] > 0.5
        favorite_accuracy = (
            (results_df.loc[favorite_mask, "actual_result"] == "home_win").mean() if favorite_mask.any() else np.nan
        )
        draw_calibration = results_df[f"{model}_draw"].mean() - (results_df["actual_result"] == "draw").mean()
        comparison_rows.append({
            "model": display_names[model],
            "n_matches": len(results_df),
            "log_loss": round(results_df[f"{model}_log_loss"].mean(), 4),
            "brier_score": round(results_df[f"{model}_brier"].mean(), 4),
            "ranked_probability_score": round(results_df[f"{model}_rps"].mean(), 4),
            "accuracy": round(accuracy, 4),
            "favorite_accuracy": round(favorite_accuracy, 4) if not np.isnan(favorite_accuracy) else "",
            "draw_calibration_bias": round(draw_calibration, 4),
            "expected_calibration_error": "",
        })
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(OUT_MODEL_COMPARISON, index=False)
    comparison_df.to_csv(OUT_BASELINE_RESULTS, index=False)
    print(f"Wrote model comparison to {OUT_MODEL_COMPARISON} and {OUT_BASELINE_RESULTS}")

    dc_exact = (results_df["dc_predicted_score"] == results_df["actual_home_goals"].astype(str) + "-" + results_df["actual_away_goals"].astype(str)).mean()

    def top_k_hit(row, k):
        try:
            scorelines = json.loads(row["dc_top10_scorelines_json"])[:k]
        except Exception:
            return False
        actual = f"{row['actual_home_goals']}-{row['actual_away_goals']}"
        return actual in [s["score"] for s in scorelines]

    top3_hit = results_df.apply(lambda r: top_k_hit(r, 3), axis=1).mean()
    top5_hit = results_df.apply(lambda r: top_k_hit(r, 5), axis=1).mean()
    dc_pred_home = results_df["dc_predicted_score"].str.split("-").str[0].astype(int)
    dc_pred_away = results_df["dc_predicted_score"].str.split("-").str[1].astype(int)
    goal_mae = ((dc_pred_home - results_df["actual_home_goals"]).abs().mean()
                + (dc_pred_away - results_df["actual_away_goals"]).abs().mean()) / 2
    total_goal_mae = ((dc_pred_home + dc_pred_away) - (results_df["actual_home_goals"] + results_df["actual_away_goals"])).abs().mean()

    scoreline_df = pd.DataFrame([{
        "model": "Dixon-Coles (main model)",
        "n_matches": len(results_df),
        "exact_score_accuracy": round(dc_exact, 4),
        "top_3_scoreline_hit_rate": round(top3_hit, 4),
        "top_5_scoreline_hit_rate": round(top5_hit, 4),
        "goal_mae": round(goal_mae, 4),
        "total_goals_mae": round(total_goal_mae, 4),
    }])
    scoreline_df.to_csv(OUT_SCORELINE_ACCURACY, index=False)
    print(f"Wrote scoreline accuracy to {OUT_SCORELINE_ACCURACY}")

    best_model = comparison_df.sort_values("log_loss").iloc[0]
    OUT_SELECTION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_SELECTION_REPORT, "w") as f:
        f.write("# EPL Model Selection Report (Phase 1 preliminary)\n\n")
        f.write(f"Rolling-origin backtest, validation seasons {VALIDATION_SEASONS[0]} to {VALIDATION_SEASONS[-1]}, "
                f"refit approximately every matchweek (10-match chronological chunks), predicting only with data "
                f"strictly before each chunk. {len(results_df)} real historical matches evaluated.\n\n")
        f.write("## Model comparison (lower log loss / Brier / RPS is better)\n\n")
        f.write(comparison_df.to_markdown(index=False))
        f.write("\n\n## Scoreline accuracy (Dixon-Coles)\n\n")
        f.write(scoreline_df.to_markdown(index=False))
        f.write(f"\n\n## Selected model\n\n**{best_model['model']}** has the lowest backtest log loss "
                f"({best_model['log_loss']}) and is used as the primary model for 2026-27 predictions. "
                f"Promoted-team Elo offset used: {promoted_elo_offset:.1f} points, derived from "
                f"{n_events} real historical promotion events.\n\n")
        f.write("## Limitations\n\n"
                "- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not "
                "every single match, for compute-time reasons; within a chunk, later matches technically use "
                "a snapshot fit before the chunk's first match rather than immediately before their own kickoff.\n"
                "- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).\n"
                "- No market-odds baseline is included in this comparison (no historical odds source with "
                "sufficient coverage was integrated in Phase 1).\n"
                "- The Dixon-Coles promoted-team offset is now leakage-safe (computed per validation season "
                "from only earlier real promotion events, and applied to that season's actual promoted clubs "
                "during backtest prediction). The **Elo** promoted-team offset is still a single global "
                "constant computed from the full historical dataset -- a smaller, documented remaining gap.\n")
    print(f"Wrote model selection report to {OUT_SELECTION_REPORT}")

    meta = make_run_metadata(
        prefix="backtest", season="2026-27",
        training_window="up to 2018-19", validation_window=f"{VALIDATION_SEASONS[0]} to {VALIDATION_SEASONS[-1]}",
        metrics=json.dumps({row["model"]: row["log_loss"] for row in comparison_rows}),
    )
    log_experiment(meta, stage="backtest", notes=f"{len(results_df)} matches evaluated")
    for row in comparison_rows:
        register_model(meta, model_name=row["model"], notes=f"log_loss={row['log_loss']}")


if __name__ == "__main__":
    main()
