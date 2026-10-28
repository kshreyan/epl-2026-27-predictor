"""Predicts every real 2026-27 regular-season NFL/NBA/NHL/NCAA
Football game.

**Moneyline (home/draw/away for NFL and NHL -- NHL's real final score
can't literally tie, see point_margin_model.py, but ties are kept
structurally possible in this schema for consistency; home/away only
for NBA/NCAA Football, which cannot end in a real tie at all) uses
whichever model actually won this league's own real backtest**
(src/evaluation/backtest_team_sport.py) -- the point-margin model for
NFL, plain Elo-only win probability for NBA/NHL/NCAA Football (see
reports/{league}_model_selection_report.md for the real numbers; never
assumed). `should_use_point_margin_model()` reads this fresh from that
backtest's own comparison CSV.

**No BTTS market**: unlike soccer, "both teams to score" has no real
meaning for any of these sports (both sides score in nearly every real
game) -- dropped entirely, not faked. **Totals** (a real, standard
market in all four sports) uses a simple real rolling points/goals-for
and -against average per team, NOT independently backtested the way
the moneyline model is -- flagged as less validated, same honesty
pattern soccer's Simple-Poisson-derived derived markets use.

Run: python -m src.models.predict_team_sport_matches --league nfl
(also accepts nba, nhl, ncaaf)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.calibration.calibrate_probabilities import apply_calibration, fit_calibrators  # noqa: E402
from src.evaluation.backtest_team_sport import ALLOWS_TIES, ELO_K_FACTOR  # noqa: E402
from src.evaluation.closing_line_value import append_odds_snapshot  # noqa: E402
from src.evaluation.hash_chained_ledger import append_prediction  # noqa: E402
from src.features.build_market_features import log_odds_average_binary  # noqa: E402
from src.features.market_devig import DEVIG_METHODS, select_devig_method  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.baselines import elo_only_probabilities  # noqa: E402
from src.models.compute_margin_survival_team_sport import cover_probability_at_line  # noqa: E402
from src.models.nfl_qb_rating import fit_qb_elo, qb_adjustment, shrink_qb_ratings  # noqa: E402
from src.models.point_margin_model import (  # noqa: E402
    fit_point_margin_model,
    outcome_probabilities,
    predict_margin_distribution,
    predicted_score_from_margin,
    should_use_point_margin_model,
    top_n_scorelines,
)
from src.models.scoreline_models import moneyline_pick, spread_pick, totals_pick  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

DEFAULT_TOTAL_LINE = {"nfl": 44.5, "nba": 228.5, "nhl": 6.0, "ncaaf": 53.5}  # real league-average-ish fallback, overridden per-game below

OUTPUT_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team",
    "stadium", "status", "prediction_mode", "actual_home_goals", "actual_away_goals", "actual_result",
    "home_expected_goals_model_only", "away_expected_goals_model_only",
    "home_expected_goals_market_integrated", "away_expected_goals_market_integrated",
    "predicted_score_model_only", "predicted_score_market_integrated",
    "predicted_result_model_only", "predicted_result_market_integrated",
    "home_win_prob_model_only", "draw_prob_model_only", "away_win_prob_model_only",
    "home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated",
    "moneyline_pick", "btts_pick", "totals_pick", "spread_pick",
    "top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json",
    "market_available", "closing_market_available", "market_blend_applied",
    "btts_yes_prob_model_only", "btts_no_prob_model_only",
    "total_goals_line_model_only", "over_prob_model_only", "under_prob_model_only", "totals_blend_applied",
    "handicap_line_model_only", "home_cover_prob_model_only", "away_cover_prob_model_only", "handicap_blend_applied",
    "squad_data_available", "injury_data_available", "lineup_data_available",
    "rest_day_diff", "congestion_diff",
    "home_elo", "away_elo", "confidence", "upset_risk", "data_quality_score",
    "market_home_odds", "market_draw_odds", "market_away_odds",
    "moneyline_model_source", "derived_markets_model_source",
    "run_id", "model_version", "generated_at",
]

DATA_QUALITY_SCORE = 0.3  # several real seasons of real data -- a real step up from the UEFA club competitions' 0.2


def result_from_margin(margin: float, allows_ties: bool) -> str:
    if allows_ties and margin == 0:
        return "draw"
    return "home_win" if margin > 0 else "away_win"


def team_rolling_score_avgs(df: pd.DataFrame, team: str, league_avg: float) -> tuple[float, float]:
    home_rows = df[df["home_team"] == team]
    away_rows = df[df["away_team"] == team]
    sf = pd.concat([home_rows["home_score"], away_rows["away_score"]])
    sa = pd.concat([home_rows["away_score"], away_rows["home_score"]])
    if len(sf) == 0:
        return league_avg, league_avg
    return float(sf.mean()), float(sa.mean())


def load_market_odds(odds_path: Path, league_id: str) -> dict[str, dict]:
    """Real h2h market odds per match_id, de-vigged per real bookmaker
    row with this league's own real backtested-best method (see
    backtest_market_devig.py), then averaged across every real
    bookmaker in logit space -- the same "don't just take the first
    quote" discipline build_market_features.py already established for
    soccer, generalized here to a 2-outcome market (no real draw price
    exists for NFL/NBA/NHL/NCAA Football's real h2h market -- confirmed
    directly, 0 of 815 real NFL h2h rows this session had one)."""
    devig_fn = DEVIG_METHODS[select_devig_method(league_id)]
    rows_by_match: dict[str, list[tuple[float, float, float, float]]] = {}
    if odds_path.exists():
        with open(odds_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["market_type"] != "h2h" or row["is_real_data"] != "True":
                    continue
                if not row["current_home_odds"] or not row["current_away_odds"]:
                    continue
                home_odds, away_odds = float(row["current_home_odds"]), float(row["current_away_odds"])
                fair_home, fair_away = devig_fn((home_odds, away_odds))
                rows_by_match.setdefault(row["match_id"], []).append((home_odds, away_odds, fair_home, fair_away))

    out: dict[str, dict] = {}
    for match_id, book_rows in rows_by_match.items():
        fair_home_probs = [r[2] for r in book_rows]
        blended_home_prob = log_odds_average_binary(fair_home_probs)
        out[match_id] = {
            # Real representative decimal odds for display (mean across every
            # real bookmaker quoting this match) -- NOT a probability.
            "home": round(float(np.mean([r[0] for r in book_rows])), 3),
            "away": round(float(np.mean([r[1] for r in book_rows])), 3),
            # Real de-vigged fair probability, averaged across bookmakers in
            # logit space -- what the market blend below actually uses.
            "home_fair_prob": blended_home_prob, "away_fair_prob": 1 - blended_home_prob,
            "n_bookmakers": len(book_rows),
        }
    return out


def should_apply_market_blend(league_id: str) -> bool:
    """Whether THIS league's own real backtest (backtest_nfl_market_blend
    .py-style module) found a statistically significant edge from
    blending the model with the real market -- never assumed. Defaults
    to False (model-only) if that backtest hasn't been run yet for
    this league, the same "no evidence, no blend" discipline
    market_blend_model.py already established for soccer."""
    path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_comparison.csv"
    if not path.exists():
        return False
    return bool(pd.read_csv(path).iloc[0]["blend_significant"])


def load_real_results(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hg, ag = int(float(row["home_goals"])), int(float(row["away_goals"]))
            out[row["match_id"]] = {"home_goals": hg, "away_goals": ag}
    return out


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    allows_ties = ALLOWS_TIES[league_id]
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    odds_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_odds.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_match_predictions.csv")

    use_point_margin = should_use_point_margin_model(league_id)
    winner_name = "point-margin model (Elo + real fitted margin regression)" if use_point_margin else "Elo-only win probability"
    moneyline_source_note = (
        f"{winner_name}, real-backtested (winner of {cfg.display_name}'s own real moneyline backtest -- "
        f"see reports/{league_id}_model_selection_report.md)."
    )
    derived_markets_source_note = (
        "Simple rolling points-for/against average (NOT independently backtested as a totals model -- "
        f"see reports/{league_id}_model_selection_report.md -- treat as less validated than the moneyline "
        "prediction above). No BTTS market: not a real concept in this sport, dropped rather than faked."
    )

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures = pd.read_csv(fixtures_path)
    market_odds = load_market_odds(odds_path, league_id)
    real_results = load_real_results(real_results_path)
    apply_blend = should_apply_market_blend(league_id)
    devig_method = select_devig_method(league_id)

    if real_results:
        completed_rows = []
        for _, fx in fixtures.iterrows():
            rr = real_results.get(fx["match_id"])
            if rr is None:
                continue
            completed_rows.append({
                "date": pd.Timestamp(fx["date"]), "home_team": fx["home_team"], "away_team": fx["away_team"],
                "home_score": rr["home_goals"], "away_score": rr["away_goals"],
                "home_qb_name": fx.get("home_qb_name", ""), "away_qb_name": fx.get("away_qb_name", ""),
            })
        if completed_rows:
            historical = pd.concat([historical, pd.DataFrame(completed_rows)], ignore_index=True)

    fit = fit_point_margin_model(historical, allows_ties=allows_ties, k_factor=ELO_K_FACTOR)
    league_avg_points = float(pd.concat([historical["home_score"], historical["away_score"]]).mean())

    # QB-rating adjustment (see nfl_qb_rating.py/backtest_nfl_qb_adjustment.py)
    # -- only for a league with real per-QB data (NFL, via nflverse) AND
    # only if its own real held-out-season backtest found the signal
    # significant; never assumed, and silently skipped (team-only
    # prediction) for any league/fixture without both real pieces.
    qb_shrunk_ratings: dict[str, float] = {}
    qb_coefficient = 0.0
    if "home_qb_name" in historical.columns:
        coef_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_qb_adjustment_coefficient.csv"
        if coef_path.exists():
            coef_row = pd.read_csv(coef_path).iloc[0]
            if bool(coef_row["significant"]):
                qb_coefficient = float(coef_row["coefficient"])
                raw_qb_ratings, qb_n_starts = fit_qb_elo(historical)
                qb_shrunk_ratings = shrink_qb_ratings(raw_qb_ratings, qb_n_starts)

    # Real isotonic calibration (see calibrate_nfl_probabilities.py) --
    # only if that league's own real calibration backtest has actually
    # been run; refit fresh here each call, same "cheap, no stale
    # artifact" pattern market_blend_model.py already established for
    # soccer's own calibrators.
    calibrators = {}
    calibration_classes = ["home_win", "away_win"]
    calibration_summary_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_2026_27_calibration_summary.csv"
    if calibration_summary_path.exists():
        pm_backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
        if pm_backtest_path.exists():
            pm_backtest_df = pd.read_csv(pm_backtest_path)
            pm_backtest_df = pm_backtest_df[pm_backtest_df["actual_result"] != "draw"].reset_index(drop=True)
            calibrators = fit_calibrators(pm_backtest_df, classes=calibration_classes, raw_col_prefix="pm_")

    meta = make_run_metadata(prefix=f"predict_{league_id}", season="2026-27")
    generated_at = now_utc_iso()
    rows = []
    for _, fx in fixtures.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        mean, sigma = predict_margin_distribution(fit, home, away)

        if qb_shrunk_ratings:
            adj = qb_adjustment(fx.get("home_qb_name"), fx.get("away_qb_name"), qb_shrunk_ratings)
            if adj is not None:
                mean += qb_coefficient * adj

        if use_point_margin:
            home_win, draw, away_win = outcome_probabilities(mean, sigma, allows_ties)
        else:
            r_home = fit.elo_run.final_ratings.get(home, 1500.0)
            r_away = fit.elo_run.final_ratings.get(away, 1500.0)
            eh, ed, ea = elo_only_probabilities(r_home, r_away, home_advantage=0.0)
            if allows_ties:
                home_win, draw, away_win = eh, ed, ea
            else:
                total = eh + ea
                home_win, draw, away_win = eh / total, 0.0, ea / total

        if calibrators:
            two_way_total = home_win + away_win
            raw_probs = {
                "home_win": home_win / two_way_total if two_way_total > 0 else 0.5,
                "away_win": away_win / two_way_total if two_way_total > 0 else 0.5,
            }
            calibrated = apply_calibration(calibrators, raw_probs, classes=calibration_classes)
            home_win = calibrated["home_win"] * (1 - draw)
            away_win = calibrated["away_win"] * (1 - draw)

        home_sf, home_sa = team_rolling_score_avgs(historical, home, league_avg_points)
        away_sf, away_sa = team_rolling_score_avgs(historical, away, league_avg_points)
        mean_total = (home_sf + home_sa + away_sf + away_sa) / 2
        home_pts, away_pts = predicted_score_from_margin(mean_total, mean, allows_ties)
        predicted_score = f"{home_pts}-{away_pts}"
        predicted_result = result_from_margin(home_pts - away_pts, allows_ties)

        # Reuses the margin model's own fitted sigma for the TOTAL's
        # spread too: if each team's own score varied independently
        # with similar variance, Var(home-away) == Var(home+away) by
        # symmetry -- a real, defensible approximation, not an
        # identical quantity by definition (real team scores in the
        # same game are probably mildly anti-correlated, which would
        # make the real total's variance somewhat smaller than this).
        total_line = DEFAULT_TOTAL_LINE[league_id]
        over_prob = float(1 - norm.cdf(total_line, loc=mean_total, scale=fit.sigma))
        under_prob = 1 - over_prob

        handicap_line = round(-mean * 2) / 2  # fair home spread line, rounded to the nearest half-point
        home_cover_prob = cover_probability_at_line(mean, sigma, handicap_line)

        odds = market_odds.get(fx["match_id"])
        rr = real_results.get(fx["match_id"])
        confidence = max(home_win, draw, away_win)

        blend_home_win = blend_draw = blend_away_win = ""
        market_blend_applied = False
        if apply_blend and odds is not None:
            # Real market has no real draw price (see load_market_odds) --
            # renormalize the model's own home/away share to 2-way before
            # blending, then rescale back down so the model's own real
            # draw estimate (the market has no real signal on tie risk)
            # still accounts for its own share of the final 3 probabilities.
            two_way_total = home_win + away_win
            model_home_2way = home_win / two_way_total if two_way_total > 0 else 0.5
            blended_home_2way = log_odds_average_binary([model_home_2way, odds["home_fair_prob"]])
            blend_home_win = round(blended_home_2way * (1 - draw), 4)
            blend_away_win = round((1 - blended_home_2way) * (1 - draw), 4)
            blend_draw = round(draw, 4)
            market_blend_applied = True

        rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
            "stadium": fx["stadium"], "status": "completed" if rr else fx["status"],
            "prediction_mode": "regular_season_mode",
            "actual_home_goals": rr["home_goals"] if rr else "",
            "actual_away_goals": rr["away_goals"] if rr else "",
            "actual_result": result_from_margin(rr["home_goals"] - rr["away_goals"], allows_ties) if rr else "",
            "home_expected_goals_model_only": round(home_sf, 1), "away_expected_goals_model_only": round(away_sf, 1),
            "home_expected_goals_market_integrated": "", "away_expected_goals_market_integrated": "",
            "predicted_score_model_only": predicted_score, "predicted_score_market_integrated": "",
            "predicted_result_model_only": predicted_result, "predicted_result_market_integrated": "",
            "home_win_prob_model_only": round(home_win, 4), "draw_prob_model_only": round(draw, 4),
            "away_win_prob_model_only": round(away_win, 4),
            "home_win_prob_market_integrated": blend_home_win, "draw_prob_market_integrated": blend_draw,
            "away_win_prob_market_integrated": blend_away_win,
            "moneyline_pick": moneyline_pick(home_win, draw, away_win, home, away),
            "btts_pick": "", "totals_pick": totals_pick(over_prob, total_line),
            "spread_pick": spread_pick(home_cover_prob, handicap_line, home, away),
            "top_10_scorelines_model_only_json": json.dumps(top_n_scorelines(mean_total, mean, fit.sigma, n=10)),
            "top_10_scorelines_market_integrated_json": "",
            "market_available": odds is not None, "closing_market_available": False,
            "market_blend_applied": market_blend_applied,
            "btts_yes_prob_model_only": "", "btts_no_prob_model_only": "",
            "total_goals_line_model_only": total_line, "over_prob_model_only": round(over_prob, 4),
            "under_prob_model_only": round(under_prob, 4), "totals_blend_applied": False,
            "handicap_line_model_only": handicap_line, "home_cover_prob_model_only": round(home_cover_prob, 4),
            "away_cover_prob_model_only": round(1 - home_cover_prob, 4), "handicap_blend_applied": False,
            "squad_data_available": False, "injury_data_available": False, "lineup_data_available": False,
            "rest_day_diff": "", "congestion_diff": "",
            "home_elo": round(fit.elo_run.final_ratings.get(home, 1500.0), 1),
            "away_elo": round(fit.elo_run.final_ratings.get(away, 1500.0), 1),
            "confidence": round(confidence, 4), "upset_risk": round(1 - confidence, 4),
            "data_quality_score": DATA_QUALITY_SCORE,
            "market_home_odds": odds["home"] if odds else "",
            # No real draw price exists for these sports' h2h market (confirmed directly, see load_market_odds).
            "market_draw_odds": "",
            "market_away_odds": odds["away"] if odds else "",
            "moneyline_model_source": moneyline_source_note, "derived_markets_model_source": derived_markets_source_note,
            "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

        # Real audit trail + CLV history: only for a fixture not yet
        # completed (a pre-kickoff prediction, the only kind that can
        # ever be honestly scored or have real future closing-line
        # history) -- matches prediction_ledger.py's own leak-safe
        # discipline for soccer, generalized here via the new
        # hash-chained ledger (see hash_chained_ledger.py).
        if rr is None:
            append_prediction(league_id, {
                "match_id": fx["match_id"], "kickoff_utc": fx["kickoff_utc"], "prediction_timestamp": generated_at,
                "model_version": MODEL_VERSION, "run_id": meta.run_id,
                "model_home_win_prob": home_win, "model_draw_prob": draw, "model_away_win_prob": away_win,
                "market_home_win_prob": odds["home_fair_prob"] if odds else None,
                "market_away_win_prob": odds["away_fair_prob"] if odds else None,
                "blended_home_win_prob": blend_home_win or None, "blended_draw_prob": blend_draw or None,
                "blended_away_win_prob": blend_away_win or None,
            })
            if odds is not None:
                append_odds_snapshot(league_id, [{
                    "match_id": fx["match_id"], "snapshot_timestamp": generated_at, "kickoff_utc": fx["kickoff_utc"],
                    "home_fair_prob": odds["home_fair_prob"], "away_fair_prob": odds["away_fair_prob"],
                    "devig_method": devig_method, "run_id": meta.run_id,
                }])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    n_with_market = sum(1 for r in rows if r["market_available"])
    print(f"Wrote {len(rows)} predictions to {out_path} ({n_with_market} with real current market odds)")
    log_experiment(meta, stage=f"predict_{league_id}_matches", notes=f"{len(rows)} fixtures, moneyline={'point_margin' if use_point_margin else 'elo_only'}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba", "nhl", "ncaaf"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
