"""Generate model-only predictions for real 2026-27 fixtures.

Mode: `preseason_mode` when run as a script (today, 2026-08-18, is
before kickoff on 2026-08-21 -- see spec section 6). Market odds,
injury reports, and lineup data are all genuinely unavailable for this
season (see config/data_sources.yaml), so `market_available`,
`injury_data_available`, and `lineup_data_available` are False on
every row and the `*_market_integrated_*` columns are left blank
rather than duplicating the model-only numbers under a misleading
label.

1X2 win/draw/loss probabilities come from the stacked ensemble
(src/models/final_stacked_model.py) only when its edge over Dixon-Coles
alone is statistically significant -- a paired-bootstrap 95% CI on the
log-loss difference that excludes zero AND a majority-of-seasons win,
checked fresh on every run, not hardcoded. On the real backtest this
is currently NOT the case (95% CI [-0.0021, +0.0087], wins 3/7
seasons -- see reports/epl_2026_27_ensemble_report.md), so predictions
fall back to isotonic-calibrated Dixon-Coles alone. An earlier version
of this pipeline used a raw point-estimate comparison and briefly
declared the ensemble primary on a 0.003 log-loss gap that turned out
to be within bootstrap noise -- fixed by requiring the stronger
criterion above. The predicted scoreline, top-10 scorelines, and
expected goals always come from Dixon-Coles' own joint distribution
regardless of which model wins the 1X2 comparison, because the
ensemble has no scoreline model of its own -- only a win/draw/loss
classifier. The full-season Monte Carlo simulation
(src/simulation/simulate_full_season.py) also always uses Dixon-Coles'
joint scoreline distribution for the same reason.

`build_model_context()` and `predict_fixtures()` are the reusable
pieces src/update_after_matchweek.py calls to re-predict the remaining
fixtures after a real matchweek's results are locked in, so the
weekly-update engine is not a second, drifting copy of this logic.

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
from src.evaluation.backtest import team_rolling_goal_avgs  # noqa: E402
from src.evaluation.prediction_ledger import append_to_ledger, load_combined_match_odds  # noqa: E402
from src.evaluation.recalibration_gate import apply_challenger, load_active_calibrators  # noqa: E402
from src.features.build_market_features import log_odds_average  # noqa: E402
from src.features.build_schedule_congestion_features import build_schedule_congestion_features  # noqa: E402
from src.models.baselines import (  # noqa: E402
    elo_only_probabilities,
    previous_season_table_baseline,
    simple_poisson_baseline,
)
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.final_stacked_model import BASE_MODELS, CLASSES, fit_final_meta_learner  # noqa: E402
from src.models.market_blend_model import evaluate_market_blend  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    compute_promoted_team_history,
    compute_promoted_team_rating_distribution,
    summarize_promoted_team_baseline,
)
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
LEDGER_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_prediction_ledger.csv"
MATCH_ODDS_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_match_odds.csv"
REAL_ODDS_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv"
ACTIVE_CALIBRATORS_PATH = REPO_ROOT / "model_registry" / "active_calibrators.pkl"
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
    "dc_raw_home_win_prob", "dc_raw_draw_prob", "dc_raw_away_win_prob",
    "home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated",
    "top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json",
    "market_available", "closing_market_available", "market_blend_applied", "squad_data_available", "injury_data_available", "lineup_data_available",
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


def build_model_context(
    df_clean: pd.DataFrame, universe: list[str], model_cfg: dict, as_of_date: pd.Timestamp,
    active_calibrators_path: Path | None = None,
) -> dict:
    """Fits Dixon-Coles + Elo on `df_clean` (real historical data, optionally
    extended with locked-in real 2026-27 results for a weekly update) and,
    if a backtest exists, the isotonic calibrators and stacked ensemble.
    Returns a context dict consumed by `predict_fixtures`."""
    promoted_elo_offset, n_events = compute_promoted_team_elo_offset(df_clean)
    promo_history = compute_promoted_team_history(df_clean)
    promo_summary = summarize_promoted_team_baseline(promo_history)
    points_shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
    # Both offsets share the sign of points_shortfall: defense[i] is
    # SUBTRACTED in the Dixon-Coles exponent, so a lower value means
    # concedes MORE, keeping attack and defense pointing the same
    # (weaker) direction for a below-average promoted team.
    dc_attack_offset = points_shortfall / 100.0
    dc_defense_offset = points_shortfall / 100.0
    # For the season SIMULATION (not these match-level predictions, which
    # still use the point-estimate offset above): promoted clubs are drawn
    # from the real cross-sectional distribution of promoted-club debut
    # ratings instead of a fixed offset -- see
    # simulate_full_season.TeamStrengthUncertainty for why (fixes a
    # double-counting bug for clubs, e.g. Ipswich Town, with real recent
    # data already reflected in their own Dixon-Coles fit).
    promoted_rating_dist = compute_promoted_team_rating_distribution(
        df_clean, l2_reg=model_cfg["dixon_coles"].get("l2_reg", 0.03),
    )

    fit = fit_dixon_coles_model(
        df_clean, universe, as_of_date, half_life_days=model_cfg["dixon_coles"]["time_decay_half_life_days"],
        l2_reg=model_cfg["dixon_coles"].get("l2_reg", 0.03),
    )
    fit = apply_promoted_team_adjustment(fit, PROMOTED_TEAMS, dc_attack_offset, dc_defense_offset)

    elo_run = run_elo(
        df_clean, promoted_offset=promoted_elo_offset,
        k_factor=model_cfg["elo"]["k_factor"], home_advantage=model_cfg["elo"]["home_advantage_elo_points"],
    )
    elo_ratings = dict(elo_run.final_ratings)
    league_avg_goals_overall = float(pd.concat([df_clean["home_goals"], df_clean["away_goals"]]).mean())

    calibrators, calibration_method, active_challenger = {}, "none", None
    ensemble_meta, ensemble_beats_dc, ensemble_metrics = None, False, {}
    if BACKTEST_PATH.exists():
        backtest_df = pd.read_csv(BACKTEST_PATH)
        calibrators = fit_calibrators(backtest_df)
        calibration_method = "isotonic" if all(c is not None for c in calibrators.values()) else "raw_fallback"

        # A promoted challenger (recalibration_gate.py) replaces the
        # static historical-only fit above -- but ONLY if a paired
        # bootstrap 95% CI showed it beating the incumbent across
        # rolling-origin real-match evaluations; see that module's
        # docstring. Below MIN_MATCHES_TO_ATTEMPT (150) real matches, no
        # challenger is ever promoted, so this file simply doesn't exist
        # yet and this is a no-op. The challenger may be temperature
        # scaling (below ISOTONIC_MIN_REAL_MATCHES) or isotonic, so it is
        # applied via apply_challenger, not apply_calibration, in
        # predict_fixtures below.
        active_path = active_calibrators_path if active_calibrators_path is not None else ACTIVE_CALIBRATORS_PATH
        active_challenger = load_active_calibrators(active_path)
        if active_challenger is not None:
            calibration_method = f"{active_challenger['method']}_promoted_challenger"

        ensemble_meta, ensemble_beats_dc, ensemble_metrics = fit_final_meta_learner(backtest_df)
        # ensemble_beats_dc requires a paired-bootstrap 95% CI that excludes
        # zero AND a season-majority win (see final_stacked_model.py) -- not
        # just a lower point-estimate log loss, which was not statistically
        # distinguishable from noise on the real backtest (see
        # reports/epl_2026_27_ensemble_report.md).
        print(f"Stacked ensemble log loss {ensemble_metrics.get('ensemble_log_loss', float('nan')):.4f} vs "
              f"Dixon-Coles {ensemble_metrics.get('dc_log_loss', float('nan')):.4f} "
              f"(bootstrap CI [{ensemble_metrics.get('bootstrap_ci_low', float('nan')):+.4f}, "
              f"{ensemble_metrics.get('bootstrap_ci_high', float('nan')):+.4f}], "
              f"{ensemble_metrics.get('season_wins', '?')}/{ensemble_metrics.get('n_seasons', '?')} seasons) -- "
              f"edge is {'statistically significant' if ensemble_beats_dc else 'NOT statistically significant'}; "
              f"{'using ensemble' if ensemble_beats_dc else 'using calibrated Dixon-Coles'} for final predictions.")

        # Checked fresh every run, same discipline as the ensemble above:
        # a 50/50 model+market log-odds blend, tested via paired
        # bootstrap against 2,660 real historical matches with real
        # market odds (see market_blend_model.py). Applied per-fixture
        # only where BOTH this is significant AND real market odds
        # actually exist for that fixture (predict_fixtures checks the
        # latter). Same precondition as the ensemble above (needs the
        # real backtest match results file) -- guarded the same way.
        market_blend_result = evaluate_market_blend()
        market_blend_significant = market_blend_result["blend_significant"]
        print(f"Model+market blend log loss {market_blend_result['blend_mean_log_loss']:.4f} vs "
              f"Dixon-Coles {market_blend_result['dc_mean_log_loss']:.4f} "
              f"(bootstrap CI [{market_blend_result['significance']['ci_low']:+.4f}, "
              f"{market_blend_result['significance']['ci_high']:+.4f}], "
              f"{market_blend_result['significance']['season_wins']}/{market_blend_result['significance']['n_seasons']} seasons) -- "
              f"edge is {'statistically significant' if market_blend_significant else 'NOT statistically significant'}; "
              f"{'blending market odds in' if market_blend_significant else 'model-only'} for fixtures with real market data.")
    else:
        market_blend_significant = False

    return {
        "fit": fit, "elo_ratings": elo_ratings, "promoted_elo_offset": promoted_elo_offset,
        "promoted_rating_dist": promoted_rating_dist,
        "league_avg_goals_overall": league_avg_goals_overall,
        "calibrators": calibrators, "calibration_method": calibration_method, "active_challenger": active_challenger,
        "ensemble_meta": ensemble_meta, "ensemble_beats_dc": ensemble_beats_dc, "ensemble_metrics": ensemble_metrics,
        "market_blend_significant": market_blend_significant,
    }


def predict_fixtures(
    fixtures_df: pd.DataFrame, ctx: dict, df_clean: pd.DataFrame, model_cfg: dict,
    prediction_mode: str, generated_at: str, run_id: str,
    match_odds_by_id: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """Core per-fixture prediction loop, shared by the preseason run
    (all 380 fixtures) and the weekly-update engine (only the remaining,
    not-yet-completed fixtures). `match_odds_by_id` (from
    prediction_ledger.load_combined_match_odds) enables the model+market
    blend for any fixture it covers -- see market_blend_model.py: a
    50/50 log-odds pool of the model's own probability and the real
    market's, applied only when `ctx["market_blend_significant"]` (a
    paired-bootstrap test against 2,660 real historical matches, same
    bar the stacked ensemble was held to, checked fresh every run) and
    real market odds exist for that specific fixture -- which, before
    kickoff, is rarely more than a handful of fixtures at a time."""
    fit = ctx["fit"]
    match_odds_by_id = match_odds_by_id or {}
    pred_rows, expl_rows = [], []

    for _, fx in fixtures_df.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        lam, mu = match_lambdas(fit, home, away)
        matrix = score_matrix(lam, mu, fit.rho)
        raw_h, raw_d, raw_a = outcome_probabilities(matrix)

        if ctx.get("active_challenger") is not None:
            calibrated = apply_challenger(ctx["active_challenger"], {"home_win": raw_h, "draw": raw_d, "away_win": raw_a})
        elif ctx["calibrators"]:
            calibrated = apply_calibration(ctx["calibrators"], {"home_win": raw_h, "draw": raw_d, "away_win": raw_a})
        else:
            calibrated = {"home_win": raw_h, "draw": raw_d, "away_win": raw_a}

        if ctx["ensemble_meta"] is not None and ctx["ensemble_beats_dc"]:
            r_home = ctx["elo_ratings"].get(home, 1500.0 + ctx["promoted_elo_offset"])
            r_away = ctx["elo_ratings"].get(away, 1500.0 + ctx["promoted_elo_offset"])
            elo_h, elo_d, elo_a = elo_only_probabilities(r_home, r_away, model_cfg["elo"]["home_advantage_elo_points"])
            ps_h, ps_d, ps_a = previous_season_table_baseline(df_clean, home, away, "2026-27")
            h_gf, h_ga = team_rolling_goal_avgs(df_clean, home)
            a_gf, a_ga = team_rolling_goal_avgs(df_clean, away)
            sp_lam, sp_mu = simple_poisson_baseline(h_gf, h_ga, a_gf, a_ga, ctx["league_avg_goals_overall"])
            sp_matrix = score_matrix(sp_lam, sp_mu, rho=0.0)
            sp_h, sp_d, sp_a = outcome_probabilities(sp_matrix)

            # base_probs tuples are (home, draw, away), matching the column
            # order final_stacked_model._feature_matrix expects per model
            # (f"{model}_home_win", f"{model}_draw", f"{model}_away_win").
            base_probs = {"dc": (raw_h, raw_d, raw_a), "elo": (elo_h, elo_d, elo_a),
                          "prevseason": (ps_h, ps_d, ps_a), "simplepoisson": (sp_h, sp_d, sp_a)}
            feature_vec = np.array([[base_probs[m][j] for m in BASE_MODELS for j in (0, 1, 2)]])
            ens_probs_arr = np.zeros(len(CLASSES))
            ens_probs_arr[ctx["ensemble_meta"].classes_] = ctx["ensemble_meta"].predict_proba(feature_vec)[0]
            class_to_idx = {c: i for i, c in enumerate(CLASSES)}
            calibrated = {
                "home_win": float(ens_probs_arr[class_to_idx["home_win"]]),
                "draw": float(ens_probs_arr[class_to_idx["draw"]]),
                "away_win": float(ens_probs_arr[class_to_idx["away_win"]]),
            }

        market_blend_applied = False
        fixture_odds = match_odds_by_id.get(fx["match_id"])
        if ctx.get("market_blend_significant") and fixture_odds is not None:
            model_tuple = (calibrated["home_win"], calibrated["draw"], calibrated["away_win"])
            market_tuple = (
                fixture_odds["home_implied_probability_no_vig"],
                fixture_odds["draw_implied_probability_no_vig"],
                fixture_odds["away_implied_probability_no_vig"],
            )
            bh, bd, ba = log_odds_average([model_tuple, market_tuple])
            calibrated = {"home_win": bh, "draw": bd, "away_win": ba}
            market_blend_applied = True

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
            "stadium": fx["stadium"], "status": fx["status"], "prediction_mode": prediction_mode,
            "actual_home_goals": "", "actual_away_goals": "", "actual_result": "",
            "home_expected_goals_model_only": round(lam, 3), "away_expected_goals_model_only": round(mu, 3),
            "home_expected_goals_market_integrated": "", "away_expected_goals_market_integrated": "",
            "predicted_score_model_only": predicted_score, "predicted_score_market_integrated": "",
            "predicted_result_model_only": predicted_result, "predicted_result_market_integrated": "",
            "home_win_prob_model_only": round(calibrated["home_win"], 4),
            "draw_prob_model_only": round(calibrated["draw"], 4),
            "away_win_prob_model_only": round(calibrated["away_win"], 4),
            # Raw (uncalibrated, pre-ensemble) Dixon-Coles probability,
            # captured unconditionally at prediction time -- this is the
            # baseline a later scoring pass compares the production
            # prediction against. Storing it now means scoring never has
            # to recompute it from a model that has since been refit on
            # real results, which would leak.
            "dc_raw_home_win_prob": round(raw_h, 4),
            "dc_raw_draw_prob": round(raw_d, 4),
            "dc_raw_away_win_prob": round(raw_a, 4),
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "top_10_scorelines_model_only_json": json.dumps(top10),
            "top_10_scorelines_market_integrated_json": "",
            "market_available": False, "closing_market_available": False,
            "market_blend_applied": market_blend_applied,
            "squad_data_available": False, "injury_data_available": False, "lineup_data_available": False,
            "home_key_absences_count": "", "away_key_absences_count": "",
            "home_expected_lineup_strength": "", "away_expected_lineup_strength": "",
            "rest_day_diff": fx.get("rest_day_diff", ""), "congestion_diff": fx.get("congestion_diff", ""),
            "model_market_disagreement": "", "confidence": round(confidence, 4), "upset_risk": upset_risk,
            "data_quality_score": DATA_QUALITY_SCORE,
            "run_id": run_id, "data_version": DATA_VERSION, "feature_version": FEATURE_VERSION,
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
            "market_disagreement_explanation": (
                "Real market odds blended in (50/50 log-odds pool, validated via paired bootstrap "
                "against 2,660 real historical matches -- see market_blend_model.py)."
                if market_blend_applied else "No real market odds available for this fixture yet -- model-only prediction."
            ),
            "squad_injury_explanation": (
                f"{'Promoted club' if home_is_promoted else 'Established club'} vs "
                f"{'promoted club' if away_is_promoted else 'established club'}; no verified injury/lineup "
                f"feed connected, so squad_injury factors are not incorporated (see data_quality_notes)."
            ),
            "schedule_congestion_explanation": f"rest_day_diff={fx.get('rest_day_diff','')}, congestion_diff={fx.get('congestion_diff','')} (matches in last 7 days, home minus away).",
            "uncertainty_explanation": (
                "Promoted-club opponent: wide team-strength uncertainty (see epl_2026_27_dynamic_team_strength.csv)."
                if home_is_promoted or away_is_promoted else "Both clubs have substantial recent EPL history informing this estimate."
            ),
            "data_quality_notes": f"data_quality_score={DATA_QUALITY_SCORE} (market/injury/lineup/squad-transfer feeds unavailable).",
            "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    return pred_rows, expl_rows


def main() -> None:
    with open(MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    ctx = build_model_context(df_clean, universe, model_cfg, as_of_date)

    fixtures_df = pd.read_csv(FIXTURES_PATH)
    congestion_df = build_schedule_congestion_features(fixtures_df)
    fixtures_df = fixtures_df.merge(congestion_df, on="match_id", how="left")

    generated_at = now_utc_iso()
    effective_method = "ensemble_stacking_logreg" if (ctx["ensemble_meta"] is not None and ctx["ensemble_beats_dc"]) else ctx["calibration_method"]
    meta = make_run_metadata(
        prefix="predict", season="2026-27",
        calibration_method=effective_method, market_weight=0.0,
        latest_source_timestamp_used=fixtures_df["source_timestamp"].max() if "source_timestamp" in fixtures_df else generated_at,
    )

    match_odds_by_id = load_combined_match_odds(REAL_ODDS_PATH, MATCH_ODDS_PATH)
    pred_rows, expl_rows = predict_fixtures(fixtures_df, ctx, df_clean, model_cfg, "preseason_mode", generated_at, meta.run_id, match_odds_by_id)

    pred_df = pd.DataFrame(pred_rows)[PREDICTION_COLUMNS]
    OUT_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(OUT_PREDICTIONS, index=False)
    print(f"Wrote {len(pred_df)} match predictions to {OUT_PREDICTIONS} "
          f"({int(pred_df['market_blend_applied'].sum())} with the model+market blend applied)")

    append_to_ledger(pred_rows, LEDGER_PATH, match_odds_by_id=match_odds_by_id)
    print(f"Appended {len(pred_rows)} pre-kickoff predictions to {LEDGER_PATH}")

    expl_df = pd.DataFrame(expl_rows)
    expl_df.to_csv(OUT_EXPLANATIONS, index=False)
    print(f"Wrote {len(expl_df)} match explanations to {OUT_EXPLANATIONS}")

    log_experiment(meta, stage="predict_all_matches", notes=f"{len(pred_df)} fixtures, method={effective_method}")


if __name__ == "__main__":
    main()
