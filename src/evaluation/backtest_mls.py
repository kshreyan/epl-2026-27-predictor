"""Rolling-origin backtest for MLS, real 2023-2025 seasons.

Not `backtest.py --league mls`: that module's VALIDATION_SEASONS is a
module-level constant of seven European "YYYY-YY" season labels
(2019/20-2025/26) -- MLS seasons are real single calendar years
("2023", "2024", "2025"), a different labeling convention entirely,
and CHUNK_SIZE=10 there is tuned to "~1 matchweek in a 20-team league"
(10 matches); MLS's real round size is ~15 matches (30 teams). This
script reuses every genuinely generic piece backtest.py itself already
depends on (fit_dixon_coles_model, the Elo/previous-season-table/
simple-Poisson baselines, the scoring functions) with MLS's own real
season structure instead.

Unlike UEFA Nations League's backtest (167 real matches, one thin
cycle), MLS has three full real closed seasons -- 1,496 real matches,
close to a domestic league's own backtest sample size -- so, unlike
Nations League, this DOES include the previous-season-table baseline
(a real, meaningful comparison here) and DOES attempt Dixon-Coles as a
serious candidate, not a doomed one -- let the real numbers below
decide, not an assumption either way.

Run: python -m src.evaluation.backtest_mls
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row, rps, team_rolling_goal_avgs  # noqa: E402
from src.models.baselines import elo_only_probabilities, previous_season_table_baseline, simple_poisson_baseline  # noqa: E402
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    compute_promoted_team_history,
    summarize_promoted_team_baseline,
)
from src.models.final_stacked_model import paired_bootstrap_significance  # noqa: E402
from src.models.scoreline_models import (  # noqa: E402
    apply_promoted_team_adjustment,
    fit_dixon_coles_model,
    match_lambdas,
    outcome_probabilities,
    score_matrix,
    top_n_scorelines,
)

LEAGUE_ID = "mls"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "mls_historical_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_fixtures.csv"
OUT_MATCH_RESULTS = REPO_ROOT / "data" / "outputs" / "mls_backtest_match_results.csv"
OUT_MODEL_COMPARISON = REPO_ROOT / "data" / "outputs" / "mls_backtest_model_comparison.csv"
OUT_REPORT = REPO_ROOT / "reports" / "mls_model_selection_report.md"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"

VALIDATION_SEASONS = ["2023", "2024", "2025"]
CHUNK_SIZE = 15  # ~1 real MLS round (30 teams / 2)

with open(MODEL_CONFIG_PATH) as _f:
    _MODEL_CFG = yaml.safe_load(_f)
HALF_LIFE_DAYS = _MODEL_CFG["dixon_coles"]["time_decay_half_life_days"]
L2_REG = _MODEL_CFG["dixon_coles"].get("l2_reg", 0.03)
ELO_K_FACTOR = _MODEL_CFG["elo"]["k_factor"]
ELO_HOME_ADVANTAGE = _MODEL_CFG["elo"]["home_advantage_elo_points"]


def main() -> None:
    # season is a real MLS calendar year ("2023") -- dtype=str so pandas
    # doesn't silently infer it as int64 (it looks numeric), which would
    # make every `df["season"] == season` string comparison below
    # against VALIDATION_SEASONS's str entries fail and skip everything.
    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"], dtype={"season": str}).sort_values("date").reset_index(drop=True)
    hist_teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    current_fixtures = pd.read_csv(FIXTURES_PATH)
    teams_2026 = sorted(set(current_fixtures["home_team"]) | set(current_fixtures["away_team"]))
    universe = sorted(set(hist_teams) | set(teams_2026))

    promoted_elo_offset, _n_events = compute_promoted_team_elo_offset(df)
    elo_run = run_elo(df, promoted_offset=promoted_elo_offset, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    elo_hist = elo_run.history.copy()
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

        # Real expansion-club detection (e.g. San Diego FC's real 2025
        # debut) -- the same "new team, no prior top-flight history"
        # situation a promoted domestic club is in, publicly known
        # before a ball is kicked, not match-outcome data.
        season_idx = all_seasons_in_order.index(season)
        prev_season = all_seasons_in_order[season_idx - 1] if season_idx > 0 else None
        expansion_this_season = teams_by_season[season] - teams_by_season[prev_season] if prev_season else set()
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
                apply_promoted_team_adjustment(dc_fit, list(expansion_this_season), season_attack_offset, season_defense_offset)
                if expansion_this_season else dc_fit
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
                if key not in elo_lookup.index:
                    continue
                elo_home_pre, elo_away_pre = elo_lookup.loc[key, "home_elo_pre"], elo_lookup.loc[key, "away_elo_pre"]
                if isinstance(elo_home_pre, pd.Series):
                    elo_home_pre, elo_away_pre = elo_home_pre.iloc[0], elo_away_pre.iloc[0]
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
                    "dc_lambda": lam, "dc_mu": mu, "dc_rho": dc_fit_for_predictions.rho,
                    "elo_home_win": eh, "elo_draw": ed, "elo_away_win": ea,
                    "prevseason_home_win": pst_h, "prevseason_draw": pst_d, "prevseason_away_win": pst_a,
                    "simplepoisson_home_win": sp_home, "simplepoisson_draw": sp_draw, "simplepoisson_away_win": sp_away,
                    "dc_log_loss": log_loss_row(dc_probs, actual), "dc_brier": brier_row(dc_probs, actual), "dc_rps": rps(dc_probs, actual),
                    "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                    "prevseason_log_loss": log_loss_row(pst_probs, actual), "prevseason_brier": brier_row(pst_probs, actual), "prevseason_rps": rps(pst_probs, actual),
                    "simplepoisson_log_loss": log_loss_row(sp_probs, actual), "simplepoisson_brier": brier_row(sp_probs, actual), "simplepoisson_rps": rps(sp_probs, actual),
                })

    results_df = pd.DataFrame(match_rows)
    OUT_MATCH_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUT_MATCH_RESULTS, index=False)
    print(f"Wrote {len(results_df)} real scored backtest matches to {OUT_MATCH_RESULTS}")

    model_names = ["dc", "elo", "prevseason", "simplepoisson"]
    display_names = {
        "dc": "Dixon-Coles (main model)", "elo": "Elo-only baseline",
        "prevseason": "Previous-season-table baseline", "simplepoisson": "Simple Poisson baseline",
    }
    comparison_rows = []
    for model in model_names:
        comparison_rows.append({
            "model": display_names[model],
            "n_matches": len(results_df),
            "log_loss": round(results_df[f"{model}_log_loss"].mean(), 4),
            "brier_score": round(results_df[f"{model}_brier"].mean(), 4),
            "ranked_probability_score": round(results_df[f"{model}_rps"].mean(), 4),
        })
    comparison = pd.DataFrame(comparison_rows).sort_values("log_loss").reset_index(drop=True)
    comparison.to_csv(OUT_MODEL_COMPARISON, index=False)
    print(f"Wrote model comparison to {OUT_MODEL_COMPARISON}")

    # Elo-only has the lowest raw point-estimate log loss, but only DC
    # produces a real scoreline distribution that can power BTTS/spread/
    # totals (Elo alone gives a 1X2 split, nothing else -- the same real
    # constraint UEFA Nations League hit). Unlike Nations League (where
    # DC was catastrophically, obviously worse -- log loss 2.97, worse
    # than random guessing), here the gap is a few points of log loss --
    # worth an actual significance test (this project's own established
    # bar for "is this edge real or noise," see final_stacked_model.py)
    # before deciding DC can't be trusted as primary.
    sig = paired_bootstrap_significance(
        results_df["elo_log_loss"].to_numpy(), results_df["dc_log_loss"].to_numpy(), results_df["season"].to_numpy(),
    )
    dc_significantly_better = sig["ci_excludes_zero"] and sig["season_majority"]
    elo_significantly_better = sig["ci_excludes_zero"] and not sig["season_majority"] and sig["point_estimate"] < 0
    if dc_significantly_better:
        primary, primary_reason = "Dixon-Coles (main model)", (
            f"Dixon-Coles has a statistically significant edge over Elo-only (paired bootstrap CI "
            f"[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], {sig['season_wins']}/{sig['n_seasons']} seasons)."
        )
    elif elo_significantly_better:
        primary, primary_reason = "Elo-only baseline", (
            f"Elo-only has a statistically significant edge over Dixon-Coles (paired bootstrap CI "
            f"[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], {sig['season_wins']}/{sig['n_seasons']} seasons) -- "
            f"BTTS/spread/totals predictions still use Dixon-Coles' scoreline distribution (Elo alone gives no "
            f"scoreline), the same real limitation as UEFA Nations League; treat those markets as less validated "
            f"than moneyline for MLS specifically."
        )
    else:
        primary, primary_reason = "Dixon-Coles (main model)", (
            f"Elo-only's lower raw log loss (paired bootstrap CI [{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], "
            f"{sig['season_wins']}/{sig['n_seasons']} seasons) is NOT statistically distinguishable from Dixon-"
            f"Coles -- Dixon-Coles is used as primary, both for consistency with every other league here and "
            f"because only its real scoreline distribution can power BTTS/spread/totals."
        )
    print(f"DC vs Elo: point_estimate={sig['point_estimate']:+.4f} (positive=DC better), "
          f"CI=[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], {sig['season_wins']}/{sig['n_seasons']} seasons -- "
          f"primary model: {primary}")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REPORT, "w") as f:
        f.write("# MLS Model Selection Report (Phase 1)\n\n")
        f.write(
            f"Rolling-origin backtest, real seasons {VALIDATION_SEASONS[0]}-{VALIDATION_SEASONS[-1]} (three full "
            f"real closed seasons -- unlike UEFA Nations League's thin one-cycle history, this is close to a "
            f"domestic league's own backtest sample size), refit approximately every real MLS round "
            f"({CHUNK_SIZE}-match chronological chunks), predicting only with data strictly before each chunk. "
            f"{len(results_df)} real historical matches evaluated.\n\n"
        )
        f.write("## Model comparison (lower log loss / Brier / RPS is better)\n\n")
        f.write(comparison.to_markdown(index=False))
        f.write(f"\n\n## Selected model\n\n**{primary}** is used as the primary model for 2026 predictions. "
                f"{primary_reason}\n\n")
        f.write(
            "## Limitations\n\n"
            "- No football-data.co.uk coverage exists for MLS -- no historical market-odds source, so no "
            "model+market blend backtest could be run; real current market odds (The Odds API) are shown "
            "alongside predictions for comparison only, not blended in.\n"
            "- Treated as a single combined 30-team table across both conferences, matching this project's "
            "existing single-table dashboard shape -- real MLS standings, qualification, and the playoff "
            "bracket are separately conference-based and are not reproduced here (see config/leagues.yaml).\n"
            "- Dixon-Coles/Elo/previous-season-table hyperparameters are reused unchanged from the domestic "
            "config (config/model_config.yaml); not independently re-tuned for MLS.\n"
            "- Expansion-club (e.g. San Diego FC) rating offset uses the same promoted-team-adjustment "
            "machinery domestic leagues use for a newly-promoted club -- a real, analogous \"no prior top-"
            "flight history\" situation, not a perfect substitute for real MLS expansion-draft/allocation data.\n"
        )
    print(f"Wrote model selection report to {OUT_REPORT}")


if __name__ == "__main__":
    main()
