"""Generate model-only predictions for all 380 real 2026-27 fixtures.

Mode: `preseason_mode` (today, 2026-08-18, is before kickoff on
2026-08-21 -- see spec section 6). Market odds, injury reports, and
lineup data are all genuinely unavailable for this season (see
config/data_sources.yaml), so `market_available`, `injury_data_available`,
and `lineup_data_available` are False on every row and the
`*_market_integrated_*` columns are left blank rather than duplicating
the model-only numbers under a misleading label.

Run: python -m src.models.predict_all_matches
(requires backtest + calibration to have been run first)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.calibration.calibrate_probabilities import apply_calibration, fit_calibrators  # noqa: E402
from src.features.build_schedule_congestion_features import build_schedule_congestion_features  # noqa: E402
from src.models.elo_model import compute_promoted_team_elo_offset  # noqa: E402
from src.models.promoted_team_adjustment import compute_promoted_team_history, summarize_promoted_team_baseline  # noqa: E402
from src.models.scoreline_models import (  # noqa: E402
    apply_promoted_team_adjustment,
    fit_dixon_coles_model,
    match_lambdas,
    outcome_probabilities,
    score_matrix,
    scoreline_entropy,
    top_n_scorelines,
)
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import (  # noqa: E402
    DATA_VERSION,
    FEATURE_VERSION,
    MODEL_VERSION,
    log_experiment,
    make_run_metadata,
    now_utc_iso,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
OUT_PREDICTIONS = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"
OUT_EXPLANATIONS = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_explanations.csv"

PROMOTED_TEAMS = ["Coventry City", "Ipswich Town", "Hull City"]

PREDICTION_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team", "stadium", "status",
    "prediction_mode", "actual_home_goals", "actual_away_goals", "actual_result",
    "home_expected_goals_model_only", "away_expected_goals_model_only",
    "home_expected_goals_market_integrated", "away_expected_goals_market_integrated",
    "predicted_score_model_only", "predicted_score_market_integrated",
    "predicted_result_model_only", "predicted_result_market_integrated",
    "home_win_prob_model_only", "draw_prob_model_only", "away_win_prob_model_only",
    "home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated",
    "top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json",
    "market_available", "closing_market_available", "squad_data_available", "injury_data_available", "lineup_data_available",
    "home_key_absences_count", "away_key_absences_count",
    "home_expected_lineup_strength", "away_expected_lineup_strength",
    "rest_day_diff", "congestion_diff", "model_market_disagreement", "confidence", "upset_risk",
    "data_quality_score", "run_id", "data_version", "feature_version", "model_version", "generated_at",
]

# Documented data-quality scoring: start at 1.0, subtract a fixed penalty
# for each genuinely-unavailable data category (see config/data_sources.yaml).
DATA_QUALITY_PENALTIES = {"market": 0.25, "injury": 0.25, "lineup": 0.20, "squad_transfer": 0.10}
DATA_QUALITY_SCORE = round(1.0 - sum(DATA_QUALITY_PENALTIES.values()), 2)


def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home_win"
    if home_goals < away_goals:
        return "away_win"
    return "draw"


def main() -> None:
    with open(MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    promoted_elo_offset, n_events = compute_promoted_team_elo_offset(df_clean)
    promo_history = compute_promoted_team_history(df_clean)
    promo_summary = summarize_promoted_team_baseline(promo_history)
    points_shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
    # Both offsets share the sign of points_shortfall (see equivalent
    # comment in src/simulation/simulate_full_season.py): defense[i] is
    # SUBTRACTED in the Dixon-Coles exponent, so a lower value means
    # concedes MORE, keeping attack and defense pointing the same
    # (weaker) direction for a below-average promoted team.
    dc_attack_offset = points_shortfall / 100.0
    dc_defense_offset = points_shortfall / 100.0

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    fit = fit_dixon_coles_model(
        df_clean, universe, as_of_date, half_life_days=model_cfg["dixon_coles"]["time_decay_half_life_days"],
    )
    fit = apply_promoted_team_adjustment(fit, PROMOTED_TEAMS, dc_attack_offset, dc_defense_offset)

    calibrators = {}
    calibration_method = "none"
    if BACKTEST_PATH.exists():
        backtest_df = pd.read_csv(BACKTEST_PATH)
        calibrators = fit_calibrators(backtest_df)
        calibration_method = "isotonic" if all(c is not None for c in calibrators.values()) else "raw_fallback"

    fixtures_df = pd.read_csv(FIXTURES_PATH)
    congestion_df = build_schedule_congestion_features(fixtures_df)
    fixtures_df = fixtures_df.merge(congestion_df, on="match_id", how="left")

    generated_at = now_utc_iso()
    meta = make_run_metadata(
        prefix="predict", season="2026-27",
        calibration_method=calibration_method, market_weight=0.0,
        latest_source_timestamp_used=fixtures_df["source_timestamp"].max() if "source_timestamp" in fixtures_df else generated_at,
    )

    pred_rows, expl_rows = [], []
    for _, fx in fixtures_df.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        lam, mu = match_lambdas(fit, home, away)
        matrix = score_matrix(lam, mu, fit.rho)
        raw_h, raw_d, raw_a = outcome_probabilities(matrix)

        if calibrators:
            calibrated = apply_calibration(calibrators, {"home_win": raw_h, "draw": raw_d, "away_win": raw_a})
        else:
            calibrated = {"home_win": raw_h, "draw": raw_d, "away_win": raw_a}

        pred_ij = max(
            ((i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])),
            key=lambda ij: matrix[ij[0], ij[1]],
        )
        predicted_score = f"{pred_ij[0]}-{pred_ij[1]}"
        predicted_result = result_from_score(pred_ij[0], pred_ij[1])
        top10 = top_n_scorelines(matrix, 10)

        confidence = max(calibrated.values())
        upset_risk = round(1 - confidence, 4)

        pred_rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
            "stadium": fx["stadium"], "status": fx["status"], "prediction_mode": "preseason_mode",
            "actual_home_goals": "", "actual_away_goals": "", "actual_result": "",
            "home_expected_goals_model_only": round(lam, 3), "away_expected_goals_model_only": round(mu, 3),
            "home_expected_goals_market_integrated": "", "away_expected_goals_market_integrated": "",
            "predicted_score_model_only": predicted_score, "predicted_score_market_integrated": "",
            "predicted_result_model_only": predicted_result, "predicted_result_market_integrated": "",
            "home_win_prob_model_only": round(calibrated["home_win"], 4),
            "draw_prob_model_only": round(calibrated["draw"], 4),
            "away_win_prob_model_only": round(calibrated["away_win"], 4),
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "top_10_scorelines_model_only_json": json.dumps(top10),
            "top_10_scorelines_market_integrated_json": "",
            "market_available": False, "closing_market_available": False,
            "squad_data_available": False, "injury_data_available": False, "lineup_data_available": False,
            "home_key_absences_count": "", "away_key_absences_count": "",
            "home_expected_lineup_strength": "", "away_expected_lineup_strength": "",
            "rest_day_diff": fx.get("rest_day_diff", ""), "congestion_diff": fx.get("congestion_diff", ""),
            "model_market_disagreement": "", "confidence": round(confidence, 4), "upset_risk": upset_risk,
            "data_quality_score": DATA_QUALITY_SCORE,
            "run_id": meta.run_id, "data_version": DATA_VERSION, "feature_version": FEATURE_VERSION,
            "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

        home_is_promoted = home in PROMOTED_TEAMS
        away_is_promoted = away in PROMOTED_TEAMS
        expl_rows.append({
            "match_id": fx["match_id"], "home_team": home, "away_team": away,
            "top_factors_favoring_home": f"Dixon-Coles attack/defense edge (lambda={lam:.2f} expected goals) plus home advantage.",
            "top_factors_favoring_draw": f"Scoreline entropy {scoreline_entropy(matrix):.2f} nats; teams of similar fitted strength." if abs(raw_h - raw_a) < 0.15 else "Model does not see this as a close match.",
            "top_factors_favoring_away": f"Dixon-Coles attack/defense edge (mu={mu:.2f} expected goals).",
            "top_factors_affecting_scoreline": f"Fitted home advantage log-coefficient={fit.home_advantage:.3f}, low-score correlation rho={fit.rho:.3f}.",
            "market_disagreement_explanation": "No verified odds feed connected in Phase 1 -- model-only prediction.",
            "squad_injury_explanation": (
                f"{'Promoted club' if home_is_promoted else 'Established club'} vs "
                f"{'promoted club' if away_is_promoted else 'established club'}; no verified injury/lineup "
                f"feed connected in Phase 1, so squad_injury factors are not incorporated (see data_quality_notes)."
            ),
            "schedule_congestion_explanation": f"rest_day_diff={fx.get('rest_day_diff','')}, congestion_diff={fx.get('congestion_diff','')} (matches in last 7 days, home minus away).",
            "uncertainty_explanation": (
                "Promoted-club opponent: wide team-strength uncertainty (see epl_2026_27_dynamic_team_strength.csv)."
                if home_is_promoted or away_is_promoted else "Both clubs have substantial recent EPL history informing this estimate."
            ),
            "data_quality_notes": f"data_quality_score={DATA_QUALITY_SCORE} (market/injury/lineup/squad-transfer feeds unavailable in Phase 1).",
            "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    pred_df = pd.DataFrame(pred_rows)[PREDICTION_COLUMNS]
    OUT_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(OUT_PREDICTIONS, index=False)
    print(f"Wrote {len(pred_df)} match predictions to {OUT_PREDICTIONS}")

    expl_df = pd.DataFrame(expl_rows)
    expl_df.to_csv(OUT_EXPLANATIONS, index=False)
    print(f"Wrote {len(expl_df)} match explanations to {OUT_EXPLANATIONS}")

    log_experiment(meta, stage="predict_all_matches", notes=f"{len(pred_df)} fixtures, calibration={calibration_method}")


if __name__ == "__main__":
    main()
