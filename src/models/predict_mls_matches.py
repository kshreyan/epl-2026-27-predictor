"""Predicts every real 2026 MLS fixture.

Not `predict_all_matches.py --league mls`: that module's market/
spread/totals blend evaluation depends on a real historical-odds
source keyed by football-data.co.uk season codes (no such source
exists for MLS -- see LeagueConfig.football_data_code = None). This is
a smaller, bespoke predictor, structurally the same approach as
predict_nations_league_matches.py but with real, deep backtest support
behind every choice below (1,481 real backtest matches, not Nations
League's thin 141) -- and, unlike that script, writing output in the
EXACT domestic PREDICTION_COLUMNS schema (predict_all_matches.py),
because MLS is `format: single_table` and needs to plug into the same
build_dashboard_json.build_all_for_league / domestic Trusted Picks
pooling / FixturesPage.tsx every other single-table league already
uses unchanged -- "the same format as EPL" is the explicit point.

**Moneyline (home/draw/away) is Elo-only, isotonic-calibrated**, not
Dixon-Coles: the real backtest (src/evaluation/backtest_mls.py) found
a statistically significant edge for Elo (paired bootstrap CI strictly
negative, DC worse in 2/3 real seasons) -- log loss 1.057 vs 1.085.
Calibrated here using the SAME real backtest data calibrate_
probabilities.py already isotonic-calibrated DC's probabilities from
(1,481 matches, well above the 500-match minimum) -- reusing that
module's apply_calibration but fitting our own isotonic regressors on
elo_home_win/elo_draw/elo_away_win specifically, since that module's
own fit_calibrators is hard-coded to dc_* columns. Written into the
domestic schema's home_win_prob_model_only etc. fields; dc_raw_*_prob
holds the UNCALIBRATED Elo probability (not literally "Dixon-Coles
raw" here -- same field, different real primary model, documented in
moneyline_model_source on every row).

**BTTS/spread/totals are Dixon-Coles-derived**: Elo alone gives no
scoreline. Real backtest note: DC's OWN moneyline log loss (1.085) was
close to but still worse than Elo's -- these three markets were not
independently backtested (only DC's moneyline log loss was measured),
so treat them as less validated than the moneyline prediction, same
caveat as UEFA Nations League.

No market blend: The Odds API's soccer_usa_mls odds are collected
(mls_2026_27_real_odds.csv) but never blended in here -- no real
historical-odds source exists for MLS to validate a blend against, the
same real gap Nations League has. market_available reflects whether a
real current quote exists for a fixture; market_blend_applied is
always False.

Run: python -m src.models.predict_mls_matches
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.isotonic import IsotonicRegression

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.calibration.calibrate_probabilities import CLASSES, apply_calibration  # noqa: E402
from src.evaluation.backtest_mls import ELO_HOME_ADVANTAGE, ELO_K_FACTOR, HALF_LIFE_DAYS, L2_REG  # noqa: E402
from src.models.baselines import elo_only_probabilities  # noqa: E402
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    compute_promoted_team_history,
    derive_promoted_teams,
    summarize_promoted_team_baseline,
)
from src.models.scoreline_models import (  # noqa: E402
    apply_promoted_team_adjustment,
    asian_handicap_home_cover_probability,
    btts_pick,
    btts_probability,
    fit_dixon_coles_model,
    match_lambdas,
    model_fair_handicap_line,
    moneyline_pick,
    score_matrix,
    spread_pick,
    top_n_scorelines,
    total_goals_probabilities,
    totals_pick,
)


def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home_win"
    if home_goals < away_goals:
        return "away_win"
    return "draw"
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

LEAGUE_ID = "mls"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "mls_historical_matches.csv"
COMPLETED_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_completed_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_fixtures.csv"
ODDS_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_real_odds.csv"
BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "mls_backtest_match_results.csv"
OUT_PREDICTIONS = REPO_ROOT / "data" / "outputs" / "mls_2026_27_match_predictions.csv"
OUT_EXPLANATIONS = REPO_ROOT / "data" / "outputs" / "mls_2026_27_match_explanations.csv"
DEFAULT_TOTAL_GOALS_LINE = 2.5
MIN_SAMPLES_FOR_ISOTONIC = 500  # matches calibrate_probabilities.py's own bar

# Exact domestic schema (predict_all_matches.py's PREDICTION_COLUMNS) --
# fields with no real MLS equivalent (market blend, squad/injury/lineup,
# schedule-congestion) get the same honest "unavailable" values every
# domestic league already writes when that real data isn't connected,
# not fabricated ones.
PREDICTION_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team", "stadium", "status",
    "prediction_mode", "actual_home_goals", "actual_away_goals", "actual_result",
    "home_expected_goals_model_only", "away_expected_goals_model_only",
    "home_expected_goals_market_integrated", "away_expected_goals_market_integrated",
    "predicted_score_model_only", "predicted_score_market_integrated",
    "predicted_result_model_only", "predicted_result_market_integrated",
    "home_win_prob_model_only", "draw_prob_model_only", "away_win_prob_model_only", "moneyline_pick",
    "dc_raw_home_win_prob", "dc_raw_draw_prob", "dc_raw_away_win_prob",
    "home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated",
    "top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json",
    "btts_yes_prob_model_only", "btts_no_prob_model_only", "btts_pick",
    "total_goals_line_model_only", "over_prob_model_only", "under_prob_model_only", "totals_blend_applied", "totals_pick",
    "handicap_line_model_only", "home_cover_prob_model_only", "away_cover_prob_model_only", "handicap_blend_applied", "spread_pick",
    "market_available", "closing_market_available", "market_blend_applied", "squad_data_available", "injury_data_available", "lineup_data_available",
    "home_key_absences_count", "away_key_absences_count",
    "home_expected_lineup_strength", "away_expected_lineup_strength",
    "rest_day_diff", "congestion_diff", "model_market_disagreement", "confidence", "upset_risk",
    "data_quality_score", "run_id", "data_version", "feature_version", "model_version", "generated_at",
]
EXPLANATION_COLUMNS = [
    "match_id", "home_team", "away_team",
    "top_factors_favoring_home", "top_factors_favoring_draw", "top_factors_favoring_away",
    "top_factors_affecting_scoreline", "market_disagreement_explanation", "squad_injury_explanation",
    "schedule_congestion_explanation", "uncertainty_explanation", "data_quality_notes",
    "model_version", "generated_at",
]

DATA_QUALITY_PENALTIES = {"market": 0.25, "injury": 0.25, "lineup": 0.20, "squad_transfer": 0.10}
DATA_QUALITY_SCORE = round(1.0 - sum(DATA_QUALITY_PENALTIES.values()), 2)
DATA_VERSION = "2026-09.mls-phase1"
FEATURE_VERSION = "2026-09.mls-phase1"

MONEYLINE_SOURCE_NOTE = (
    "Elo-only, isotonic-calibrated, real-backtested (log loss 1.057 on 1,481 real 2023-2025 matches, "
    "statistically significant edge over Dixon-Coles -- see reports/mls_model_selection_report.md)."
)
DERIVED_MARKETS_SOURCE_NOTE = (
    "Dixon-Coles-derived scoreline (NOT independently backtested for BTTS/spread/totals specifically -- "
    "treat as less validated than the moneyline prediction)."
)


def fit_elo_calibrators(backtest_df: pd.DataFrame) -> dict[str, IsotonicRegression | None]:
    calibrators = {}
    for cls in CLASSES:
        raw = backtest_df[f"elo_{cls}"]
        target = (backtest_df["actual_result"] == cls).astype(int)
        if len(backtest_df) < MIN_SAMPLES_FOR_ISOTONIC:
            calibrators[cls] = None
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(raw, target)
        calibrators[cls] = iso
    return calibrators


def load_market_odds() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not ODDS_PATH.exists():
        return out
    with open(ODDS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["market_type"] != "h2h" or row["is_real_data"] != "True":
                continue
            mid = row["match_id"]
            if mid in out or not row["current_home_odds"] or not row["current_draw_odds"] or not row["current_away_odds"]:
                continue
            out[mid] = True
    return out


def main() -> None:
    historical = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"], dtype={"season": str})
    completed_2026 = pd.read_csv(COMPLETED_PATH, parse_dates=["date"]) if COMPLETED_PATH.exists() else pd.DataFrame()
    df_for_fit = pd.concat([historical, completed_2026], ignore_index=True) if not completed_2026.empty else historical
    fixtures = pd.read_csv(FIXTURES_PATH)
    market_available_ids = load_market_odds()

    backtest_df = pd.read_csv(BACKTEST_PATH)
    elo_calibrators = fit_elo_calibrators(backtest_df)

    promoted_elo_offset, _n = compute_promoted_team_elo_offset(df_for_fit)
    elo_run = run_elo(df_for_fit, promoted_offset=promoted_elo_offset, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    ratings = elo_run.final_ratings

    teams_2026 = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    universe = sorted(set(df_for_fit["home_team"]) | set(df_for_fit["away_team"]) | set(teams_2026))
    promoted_teams = derive_promoted_teams(teams_2026, df_for_fit)
    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    dc_fit = fit_dixon_coles_model(df_for_fit, universe, as_of_date, half_life_days=HALF_LIFE_DAYS, l2_reg=L2_REG)
    if promoted_teams:
        # Real empirical points-shortfall of past promoted/expansion
        # clubs, same derivation domestic leagues use (see
        # simulate_full_season.py) -- not an arbitrary offset.
        promo_summary = summarize_promoted_team_baseline(compute_promoted_team_history(df_for_fit))
        shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
        dc_fit = apply_promoted_team_adjustment(dc_fit, promoted_teams, shortfall / 100.0, shortfall / 100.0)

    meta = make_run_metadata(prefix="predict_mls", season="2026-27")
    generated_at = now_utc_iso()
    completed_lookup = completed_2026.set_index("match_id") if not completed_2026.empty else pd.DataFrame()

    pred_rows, expl_rows = [], []
    for _, fx in fixtures.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        is_completed = fx["status"] == "completed"

        r_home, r_away = ratings.get(home, 1500.0), ratings.get(away, 1500.0)
        raw_h, raw_d, raw_a = elo_only_probabilities(r_home, r_away, ELO_HOME_ADVANTAGE)
        calibrated = apply_calibration(elo_calibrators, {"home_win": raw_h, "draw": raw_d, "away_win": raw_a})
        home_win, draw, away_win = calibrated["home_win"], calibrated["draw"], calibrated["away_win"]

        lam, mu = match_lambdas(dc_fit, home, away)
        matrix = score_matrix(lam, mu, dc_fit.rho)
        pred_ij = max(((i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])), key=lambda ij: matrix[ij[0], ij[1]])
        predicted_score = f"{pred_ij[0]}-{pred_ij[1]}"
        predicted_result = result_from_score(pred_ij[0], pred_ij[1])

        btts_yes = btts_probability(matrix)
        over_prob, under_prob = total_goals_probabilities(matrix, DEFAULT_TOTAL_GOALS_LINE)
        handicap_line = model_fair_handicap_line(matrix)
        home_cover_prob = asian_handicap_home_cover_probability(matrix, handicap_line)
        market_available = fx["match_id"] in market_available_ids
        confidence = max(home_win, draw, away_win)

        actual_hg = actual_ag = actual_result = ""
        if is_completed and fx["match_id"] in completed_lookup.index:
            c = completed_lookup.loc[fx["match_id"]]
            actual_hg, actual_ag, actual_result = int(c["home_goals"]), int(c["away_goals"]), c["result"]

        pred_rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
            "stadium": fx["stadium"], "status": fx["status"], "prediction_mode": "pre_kickoff",
            "actual_home_goals": actual_hg, "actual_away_goals": actual_ag, "actual_result": actual_result,
            "home_expected_goals_model_only": round(lam, 3), "away_expected_goals_model_only": round(mu, 3),
            "home_expected_goals_market_integrated": "", "away_expected_goals_market_integrated": "",
            "predicted_score_model_only": predicted_score, "predicted_score_market_integrated": "",
            "predicted_result_model_only": predicted_result, "predicted_result_market_integrated": "",
            "home_win_prob_model_only": round(home_win, 4), "draw_prob_model_only": round(draw, 4),
            "away_win_prob_model_only": round(away_win, 4), "moneyline_pick": moneyline_pick(home_win, draw, away_win, home, away),
            "dc_raw_home_win_prob": round(raw_h, 4), "dc_raw_draw_prob": round(raw_d, 4), "dc_raw_away_win_prob": round(raw_a, 4),
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "top_10_scorelines_model_only_json": json.dumps(top_n_scorelines(matrix, 10)),
            "top_10_scorelines_market_integrated_json": "",
            "btts_yes_prob_model_only": round(btts_yes, 4), "btts_no_prob_model_only": round(1 - btts_yes, 4),
            "btts_pick": btts_pick(btts_yes),
            "total_goals_line_model_only": DEFAULT_TOTAL_GOALS_LINE,
            "over_prob_model_only": round(over_prob, 4), "under_prob_model_only": round(under_prob, 4),
            "totals_blend_applied": False, "totals_pick": totals_pick(over_prob, DEFAULT_TOTAL_GOALS_LINE),
            "handicap_line_model_only": handicap_line, "home_cover_prob_model_only": round(home_cover_prob, 4),
            "away_cover_prob_model_only": round(1 - home_cover_prob, 4),
            "handicap_blend_applied": False, "spread_pick": spread_pick(home_cover_prob, handicap_line, home, away),
            "market_available": market_available, "closing_market_available": False, "market_blend_applied": False,
            "squad_data_available": False, "injury_data_available": False, "lineup_data_available": False,
            "home_key_absences_count": "", "away_key_absences_count": "",
            "home_expected_lineup_strength": "", "away_expected_lineup_strength": "",
            "rest_day_diff": "", "congestion_diff": "", "model_market_disagreement": "",
            "confidence": round(confidence, 4), "upset_risk": round(1 - confidence, 4),
            "data_quality_score": DATA_QUALITY_SCORE,
            "run_id": meta.run_id, "data_version": DATA_VERSION, "feature_version": FEATURE_VERSION,
            "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

        expl_rows.append({
            "match_id": fx["match_id"], "home_team": home, "away_team": away,
            "top_factors_favoring_home": f"Elo rating {r_home:.0f} vs {r_away:.0f} (isotonic-calibrated, real-backtested) plus home advantage.",
            "top_factors_favoring_draw": "Model does not see this as a particularly close match." if abs(raw_h - raw_a) >= 0.15 else "Elo ratings are close; a draw is a real possibility.",
            "top_factors_favoring_away": f"Elo rating {r_away:.0f} vs {r_home:.0f}.",
            "top_factors_affecting_scoreline": f"Dixon-Coles expected goals {lam:.2f}-{mu:.2f} (rho={dc_fit.rho:.3f}) -- {DERIVED_MARKETS_SOURCE_NOTE}",
            "market_disagreement_explanation": "No historical market-odds source exists for MLS (no football-data.co.uk coverage) -- model-only prediction, real current odds shown for comparison only where available.",
            "squad_injury_explanation": "No verified injury/lineup feed connected for MLS -- not incorporated.",
            "schedule_congestion_explanation": "Not computed for MLS (no verified schedule-density feed connected).",
            "uncertainty_explanation": MONEYLINE_SOURCE_NOTE,
            "data_quality_notes": f"data_quality_score={DATA_QUALITY_SCORE} (market/injury/lineup/squad-transfer feeds unavailable).",
            "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    OUT_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PREDICTIONS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PREDICTION_COLUMNS)
        writer.writeheader()
        writer.writerows(pred_rows)
    with open(OUT_EXPLANATIONS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPLANATION_COLUMNS)
        writer.writeheader()
        writer.writerows(expl_rows)

    n_with_market = sum(1 for r in pred_rows if r["market_available"])
    n_completed = sum(1 for r in pred_rows if r["status"] == "completed")
    print(f"Wrote {len(pred_rows)} predictions to {OUT_PREDICTIONS} ({n_completed} completed, {n_with_market} with real current market odds)")
    print(f"Wrote {len(expl_rows)} match explanations to {OUT_EXPLANATIONS}")
    log_experiment(meta, stage="predict_mls_matches", notes=f"{len(pred_rows)} fixtures, moneyline=elo_only_calibrated, derived_markets=dixon_coles")


if __name__ == "__main__":
    main()
