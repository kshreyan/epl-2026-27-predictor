"""Predicts every real 2026-27 league-phase fixture for a UEFA club
competition (UCL, UEL, UECL). Generalizes the old, now-removed
predict_nations_league_matches.py (one competition) to three,
parameterized by --league.

**Moneyline (home/draw/away) is Elo-only**, not Dixon-Coles: the real
backtest (src/evaluation/backtest_continental_cup.py) found Elo beats
Dixon-Coles clearly for all three competitions (log loss ~0.97-1.26
for Elo vs ~1.07-1.26 for Dixon-Coles -- see
reports/{league}_model_selection_report.md) -- the same pattern as the
old Nations League backtest, though less extreme. Elo is the trusted,
backtested primary model; its real log loss here is close to domestic-
league quality (EPL's own is 0.9865).

**BTTS/spread/totals are Simple-Poisson-derived**, not Elo-derived:
Elo alone gives no scoreline, only a 1X2 split, so it cannot power
markets that need a real goal-expectation matrix. Simple Poisson was
NOT separately backtested for these specific markets (only its
moneyline log loss was scored, and it was clearly worse than Elo) --
these three markets are therefore less validated than moneyline.

Real current market odds (The Odds API) are attached for comparison
only, never blended in: there is no real historical-odds source for
this competition to validate a blend against.

Run: python -m src.models.predict_continental_cup_matches --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import team_rolling_goal_avgs  # noqa: E402
from src.evaluation.backtest_continental_cup import ELO_HOME_ADVANTAGE, ELO_K_FACTOR  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.baselines import elo_only_probabilities, simple_poisson_baseline  # noqa: E402
from src.models.cross_competition_elo import cross_competition_seed_ratings, should_use_domestic_seed  # noqa: E402
from src.models.elo_model import run_elo  # noqa: E402
from src.models.scoreline_models import (  # noqa: E402
    asian_handicap_home_cover_probability,
    btts_pick,
    btts_probability,
    model_fair_handicap_line,
    moneyline_pick,
    outcome_probabilities,
    score_matrix,
    spread_pick,
    top_n_scorelines,
    total_goals_probabilities,
    totals_pick,
)
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

DEFAULT_TOTAL_GOALS_LINE = 2.5

# Column names match the domestic predict_all_matches.py / "_model_only"
# schema exactly (not the old, now-removed predict_nations_league_matches.py's
# bare-field naming) so the site's FixturesPage.tsx (and MatchPredictionRow
# in site/src/lib/types.ts) need zero changes to render these leagues.
# "_market_integrated" columns are always null (no validated market blend
# exists for this competition -- same honest-null pattern every other
# league uses while market_blend_applied is False), not duplicated
# model-only values.
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

# Thin-sample, uncalibrated, no squad/injury/lineup feed -- same honest
# low constant every preseason-era domestic prediction used before more
# signal existed, not a precisely-estimated figure.
DATA_QUALITY_SCORE = 0.2


def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home_win"
    if home_goals < away_goals:
        return "away_win"
    return "draw"


def load_market_odds(odds_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not odds_path.exists():
        return out
    with open(odds_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["market_type"] != "h2h" or row["is_real_data"] != "True":
                continue
            mid = row["match_id"]
            if mid in out:
                continue
            if not row["current_home_odds"] or not row["current_draw_odds"] or not row["current_away_odds"]:
                continue
            out[mid] = {
                "home": float(row["current_home_odds"]), "draw": float(row["current_draw_odds"]),
                "away": float(row["current_away_odds"]),
            }
    return out


def load_real_results(completed_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not completed_path.exists():
        return out
    with open(completed_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hg, ag = int(float(row["home_goals"])), int(float(row["away_goals"]))
            out[row["match_id"]] = {"home_goals": hg, "away_goals": ag, "result": result_from_score(hg, ag)}
    return out


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    odds_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_odds.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_match_predictions.csv")

    use_domestic_seed = should_use_domestic_seed(league_id)
    seed_note = (
        " Seeded from real domestic-league Elo where one exists (see src/models/cross_competition_elo.py) "
        "-- this competition's own real backtest found that helps here."
        if use_domestic_seed else
        " Flat-start (no domestic-Elo seed): this competition's own real backtest found the domestic-seeded "
        "variant does NOT beat it here, unlike some of the other UEFA club competitions this project covers."
    )
    moneyline_source_note = (
        f"Elo-only, real-backtested (best of up to 4 models tested on {cfg.display_name}'s real "
        f"2024-25+2025-26 league-phase data -- see reports/{league_id}_model_selection_report.md)."
        f"{seed_note}"
    )
    derived_markets_source_note = (
        "Simple-Poisson-derived scoreline (NOT independently backtested for BTTS/spread/totals specifically "
        f"-- its own moneyline log loss was clearly worse than Elo's -- see "
        f"reports/{league_id}_model_selection_report.md -- treat as less validated than the moneyline "
        "prediction above)."
    )

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures = pd.read_csv(fixtures_path)
    market_odds = load_market_odds(odds_path)
    real_results = load_real_results(real_results_path)

    # Fold real, completed 2026-27 league-phase matches into the same
    # pool used to fit Elo/rolling goal averages, so ratings/form move
    # as the league phase progresses rather than staying frozen on the
    # historical cycles.
    if real_results:
        completed_rows = []
        for _, fx in fixtures.iterrows():
            rr = real_results.get(fx["match_id"])
            if rr is None:
                continue
            completed_rows.append({
                "season": "2026-27", "match_id": fx["match_id"], "date": pd.Timestamp(fx["date"]),
                "home_team": fx["home_team"], "away_team": fx["away_team"],
                "home_goals": rr["home_goals"], "away_goals": rr["away_goals"],
            })
        if completed_rows:
            historical = pd.concat([historical, pd.DataFrame(completed_rows)], ignore_index=True)

    # "Today's" live domestic ratings are correct to use here (not
    # backtest_continental_cup.py's leak-free historical-window seed):
    # this is predicting real future matches, so every currently
    # available real result is fair game.
    seed_ratings = cross_competition_seed_ratings() if use_domestic_seed else None
    elo_run = run_elo(historical, seed_ratings=seed_ratings, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    ratings = elo_run.final_ratings

    league_avg_goals = float(pd.concat([historical["home_goals"], historical["away_goals"]]).mean())

    meta = make_run_metadata(prefix=f"predict_{league_id}", season="2026-27")
    generated_at = now_utc_iso()
    rows = []
    for _, fx in fixtures.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        r_home = ratings.get(home, 1500.0)
        r_away = ratings.get(away, 1500.0)
        home_win, draw, away_win = elo_only_probabilities(r_home, r_away, ELO_HOME_ADVANTAGE)

        h_gf, h_ga = team_rolling_goal_avgs(historical, home)
        a_gf, a_ga = team_rolling_goal_avgs(historical, away)
        lam, mu = simple_poisson_baseline(h_gf, h_ga, a_gf, a_ga, league_avg_goals)
        matrix = score_matrix(lam, mu, rho=0.0)
        pred_ij = max(((i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])), key=lambda ij: matrix[ij[0], ij[1]])
        predicted_score = f"{pred_ij[0]}-{pred_ij[1]}"

        btts_yes = btts_probability(matrix)
        over_prob, under_prob = total_goals_probabilities(matrix, DEFAULT_TOTAL_GOALS_LINE)
        handicap_line = model_fair_handicap_line(matrix)
        home_cover_prob = asian_handicap_home_cover_probability(matrix, handicap_line)

        odds = market_odds.get(fx["match_id"])
        rr = real_results.get(fx["match_id"])
        confidence = max(home_win, draw, away_win)

        rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
            "stadium": fx["stadium"], "status": "completed" if rr else fx["status"],
            "prediction_mode": "league_phase_mode",
            "actual_home_goals": rr["home_goals"] if rr else "",
            "actual_away_goals": rr["away_goals"] if rr else "",
            "actual_result": rr["result"] if rr else "",
            "home_expected_goals_model_only": round(lam, 3), "away_expected_goals_model_only": round(mu, 3),
            "home_expected_goals_market_integrated": "", "away_expected_goals_market_integrated": "",
            "predicted_score_model_only": predicted_score, "predicted_score_market_integrated": "",
            "predicted_result_model_only": result_from_score(*pred_ij), "predicted_result_market_integrated": "",
            "home_win_prob_model_only": round(home_win, 4), "draw_prob_model_only": round(draw, 4),
            "away_win_prob_model_only": round(away_win, 4),
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "moneyline_pick": moneyline_pick(home_win, draw, away_win, home, away),
            "btts_pick": btts_pick(btts_yes), "totals_pick": totals_pick(over_prob, DEFAULT_TOTAL_GOALS_LINE),
            "spread_pick": spread_pick(home_cover_prob, handicap_line, home, away),
            "home_elo": round(r_home, 1), "away_elo": round(r_away, 1),
            "top_10_scorelines_model_only_json": json.dumps(top_n_scorelines(matrix, 10)),
            "top_10_scorelines_market_integrated_json": "",
            "market_available": odds is not None, "closing_market_available": False, "market_blend_applied": False,
            "btts_yes_prob_model_only": round(btts_yes, 4), "btts_no_prob_model_only": round(1 - btts_yes, 4),
            "total_goals_line_model_only": DEFAULT_TOTAL_GOALS_LINE,
            "over_prob_model_only": round(over_prob, 4), "under_prob_model_only": round(under_prob, 4),
            "totals_blend_applied": False,
            "handicap_line_model_only": handicap_line, "home_cover_prob_model_only": round(home_cover_prob, 4),
            "away_cover_prob_model_only": round(1 - home_cover_prob, 4), "handicap_blend_applied": False,
            "squad_data_available": False, "injury_data_available": False, "lineup_data_available": False,
            "rest_day_diff": "", "congestion_diff": "",
            "confidence": round(confidence, 4), "upset_risk": round(1 - confidence, 4),
            "data_quality_score": DATA_QUALITY_SCORE,
            "market_home_odds": odds["home"] if odds else "", "market_draw_odds": odds["draw"] if odds else "",
            "market_away_odds": odds["away"] if odds else "",
            "moneyline_model_source": moneyline_source_note, "derived_markets_model_source": derived_markets_source_note,
            "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    n_with_market = sum(1 for r in rows if r["market_available"])
    print(f"Wrote {len(rows)} predictions to {out_path} ({n_with_market} with real current market odds)")
    log_experiment(meta, stage=f"predict_{league_id}_matches", notes=f"{len(rows)} fixtures, moneyline=elo_only, derived_markets=simple_poisson")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
