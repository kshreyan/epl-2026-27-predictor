"""Predicts every real 2026-27 UEFA Nations League fixture.

Not `predict_all_matches.py --league nations_league`: that module's
market/spread/totals blend evaluation depends on a real historical-
odds source keyed by football-data.co.uk season codes (no such source
exists for this competition -- see LeagueConfig.football_data_code =
None), and its ensemble-stacking path needs far more real backtest
data than 141 matches to fit safely. This is a smaller, bespoke
predictor sized to what this competition's real data actually
supports.

**Moneyline (home/draw/away) is Elo-only**, not Dixon-Coles: the real
backtest (src/evaluation/backtest_nations_league.py) found Dixon-Coles
badly overfits with only ~50-100 real prior matches to fit ~110
parameters (54 teams x attack+defense) from at early rounds -- log
loss 2.97, worse than random guessing (ln(3)=1.10). Elo-only won
clearly (log loss 1.04, in line with domestic leagues' real
performance) and is used as the trusted, backtested primary model.

**BTTS/spread/totals are Simple-Poisson-derived**, not Elo-derived:
Elo alone gives no scoreline, only a 1X2 split, so it cannot power
markets that need a real goal-expectation matrix. Simple Poisson
(team_rolling_goal_avgs -> lambda/mu -> score_matrix) is real but was
NOT separately backtested for these specific markets (only its
moneyline log loss was scored, and it was clearly worse than Elo --
1.50 vs 1.04) -- these three markets are therefore genuinely less
validated than moneyline, and every output built from this script must
say so, not present all four markets as equally trustworthy.

Real current market odds (The Odds API) are attached for comparison
only, never blended in: there is no real historical-odds source for
this competition to validate a blend against (see the backtest
report's Limitations).

Run: python -m src.models.predict_nations_league_matches
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_nations_league import (  # noqa: E402
    ELO_HOME_ADVANTAGE,
    ELO_K_FACTOR,
    team_tier_seed_ratings,
)
from src.evaluation.backtest import team_rolling_goal_avgs  # noqa: E402
from src.models.baselines import elo_only_probabilities, simple_poisson_baseline  # noqa: E402
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

LEAGUE_ID = "nations_league"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "nations_league_historical_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "nations_league_2026_27_fixtures.csv"
ODDS_PATH = REPO_ROOT / "data" / "raw" / "nations_league_2026_27_real_odds.csv"
OUT_PATH = REPO_ROOT / "data" / "outputs" / "nations_league_2026_27_match_predictions.csv"
DEFAULT_TOTAL_GOALS_LINE = 2.5

OUTPUT_COLUMNS = [
    "match_id", "season", "matchweek", "group", "date", "kickoff_utc", "home_team", "away_team",
    "stadium", "status", "actual_home_goals", "actual_away_goals", "actual_result",
    "home_win_prob", "draw_prob", "away_win_prob", "moneyline_pick",
    "home_elo", "away_elo",
    "predicted_score", "top_10_scorelines_json",
    "btts_yes_prob", "btts_no_prob", "btts_pick",
    "total_goals_line", "over_prob", "under_prob", "totals_pick",
    "handicap_line", "home_cover_prob", "away_cover_prob", "spread_pick",
    "market_available", "market_home_odds", "market_draw_odds", "market_away_odds",
    "moneyline_model_source", "derived_markets_model_source",
    "run_id", "model_version", "generated_at",
]

MONEYLINE_SOURCE_NOTE = (
    "Elo-only, real-backtested (log loss 1.04 on 141 real 2024-25 matches, best of 3 models tested -- "
    "see reports/nations_league_model_selection_report.md)."
)
DERIVED_MARKETS_SOURCE_NOTE = (
    "Simple-Poisson-derived scoreline (NOT independently backtested for BTTS/spread/totals specifically "
    "-- its own moneyline log loss, 1.50, was clearly worse than Elo's 1.04 -- treat as less validated "
    "than the moneyline prediction above)."
)


def load_market_odds() -> dict[str, dict]:
    """match_id -> best real current h2h odds (first real bookmaker row
    found per match; The Odds API returns per-bookmaker rows, and this
    project's other odds consumers already treat "a real quote exists"
    as sufficient rather than picking a single "best" price)."""
    out: dict[str, dict] = {}
    if not ODDS_PATH.exists():
        return out
    with open(ODDS_PATH, newline="", encoding="utf-8") as f:
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


def main() -> None:
    historical = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    fixtures = pd.read_csv(FIXTURES_PATH)
    market_odds = load_market_odds()

    # Seeded from each team's real 2024-25 League A/B/C/D tier (see
    # backtest_nations_league.team_tier_seed_ratings): teams in
    # different tiers rarely or never actually play each other within
    # a cycle, so nothing in a flat 1500-seed run of the real 2024-25
    # matches alone would ever correct a cross-tier rating inversion
    # (confirmed directly: a flat seed put Switzerland, a real League A
    # side, below San Marino). Two 2026-27 group-stage opponents CAN be
    # teams that were in different 2024-25 tiers (e.g. Switzerland,
    # relegated out of League A, now meets League-C-promoted North
    # Macedonia in the same 2026-27 group) -- this seed is exactly what
    # lets their final ratings reflect that real difference.
    elo_run = run_elo(historical, seed_ratings=team_tier_seed_ratings(historical), k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    ratings = elo_run.final_ratings

    league_avg_goals = float(pd.concat([historical["home_goals"], historical["away_goals"]]).mean())

    meta = make_run_metadata(prefix="predict_nations_league", season="2026-27")
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

        rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"], "group": fx["group"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
            "stadium": fx["stadium"], "status": fx["status"],
            "actual_home_goals": "", "actual_away_goals": "", "actual_result": "",
            "home_win_prob": round(home_win, 4), "draw_prob": round(draw, 4), "away_win_prob": round(away_win, 4),
            "moneyline_pick": moneyline_pick(home_win, draw, away_win, home, away),
            "home_elo": round(r_home, 1), "away_elo": round(r_away, 1),
            "predicted_score": predicted_score, "top_10_scorelines_json": json.dumps(top_n_scorelines(matrix, 10)),
            "btts_yes_prob": round(btts_yes, 4), "btts_no_prob": round(1 - btts_yes, 4), "btts_pick": btts_pick(btts_yes),
            "total_goals_line": DEFAULT_TOTAL_GOALS_LINE, "over_prob": round(over_prob, 4), "under_prob": round(under_prob, 4),
            "totals_pick": totals_pick(over_prob, DEFAULT_TOTAL_GOALS_LINE),
            "handicap_line": handicap_line, "home_cover_prob": round(home_cover_prob, 4),
            "away_cover_prob": round(1 - home_cover_prob, 4),
            "spread_pick": spread_pick(home_cover_prob, handicap_line, home, away),
            "market_available": odds is not None,
            "market_home_odds": odds["home"] if odds else "", "market_draw_odds": odds["draw"] if odds else "",
            "market_away_odds": odds["away"] if odds else "",
            "moneyline_model_source": MONEYLINE_SOURCE_NOTE, "derived_markets_model_source": DERIVED_MARKETS_SOURCE_NOTE,
            "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    n_with_market = sum(1 for r in rows if r["market_available"])
    print(f"Wrote {len(rows)} predictions to {OUT_PATH} ({n_with_market} with real current market odds)")
    log_experiment(meta, stage="predict_nations_league_matches", notes=f"{len(rows)} fixtures, moneyline=elo_only, derived_markets=simple_poisson")


if __name__ == "__main__":
    main()
