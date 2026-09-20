"""Builds data/outputs/dashboard/international_trusted_picks.json: the
UEFA Nations League equivalent of the domestic Trusted Picks table
(build_trusted_picks_json.py), scoped to its own competition.

**Moneyline only**, unlike the domestic table (which pools moneyline,
BTTS, spread, and totals): predict_nations_league_matches.py's BTTS/
spread/totals predictions are Simple-Poisson-derived and were never
independently backtested for those specific markets (only Simple
Poisson's own, clearly worse, moneyline log loss -- 1.50 vs Elo's 1.04
-- was ever measured; see reports/nations_league_model_selection_
report.md). Presenting those alongside the real-backtested Elo
moneyline picks as equally "trusted" would overstate confidence this
project can't actually back up -- everything in this table is real
Elo-only moneyline, this competition's one genuinely validated market.

Ranked by **edge over baseline** (pick probability minus 1/3, the
naive 3-way moneyline baseline), same method the domestic table uses,
for the same reason: comparable across matches regardless of how
lopsided any single match's raw probability happens to be.

Weeks are real calendar weeks (Monday-start, by each match's own real
kickoff date). Unlike the domestic table, every real 2026-27 fixture
(both the September-October and November international breaks) is
already in scope -- the whole competition is 6 real match rounds
across ~2 months, not a 34-round season stretching months past any
single break, so there is no "far off, not really forward-looking yet"
horizon problem to cut off the way the domestic table has.

Run: python -m src.dashboard.build_international_trusted_picks_json
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.dashboard.build_trusted_picks_json import _week_start  # noqa: E402
from src.dashboard.build_dashboard_json import DASHBOARD_DIR  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

LEAGUE_ID = "nations_league"
OUT_DIR = REPO_ROOT / "data" / "outputs"
PREDICTIONS_PATH = OUT_DIR / "nations_league_2026_27_match_predictions.csv"
TOP_N_PER_WEEK = 15
MONEYLINE_BASELINE = 1.0 / 3.0


def _moneyline_candidate(row: pd.Series) -> dict:
    probs = {"home": row["home_win_prob"], "draw": row["draw_prob"], "away": row["away_win_prob"]}
    side = max(probs, key=probs.get)
    probability = probs[side]
    outcome = None
    if row["status"] == "completed" and isinstance(row.get("actual_result"), str) and row["actual_result"]:
        actual_side = {"home_win": "home", "draw": "draw", "away_win": "away"}[row["actual_result"]]
        outcome = "win" if side == actual_side else "loss"
    return {
        "pick": row["moneyline_pick"], "probability": round(float(probability), 4),
        "edge": round(float(probability) - MONEYLINE_BASELINE, 4), "outcome": outcome,
    }


def _write(payload: dict) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_DIR / "international_trusted_picks.json", "w") as f:
        json.dump(payload, f, indent=2, default=str, allow_nan=False)
    print(f"Wrote international_trusted_picks.json ({len(payload.get('weeks', []))} week(s))")


def build_international_trusted_picks() -> None:
    if not PREDICTIONS_PATH.exists():
        _write({
            "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "weeks": [],
            "status": "not_yet_available", "note": "No predictions yet -- run predict_nations_league_matches.py first.",
        })
        return

    df = pd.read_csv(PREDICTIONS_PATH)
    df["kickoff_utc"] = pd.to_datetime(df["kickoff_utc"], utc=True)

    rows = []
    for _, row in df.iterrows():
        c = _moneyline_candidate(row)
        actual_score = None
        if row["status"] == "completed" and pd.notna(row.get("actual_home_goals")):
            actual_score = f"{int(row['actual_home_goals'])}-{int(row['actual_away_goals'])}"
        rows.append({
            "week_start": _week_start(row["kickoff_utc"]),
            "match_id": row["match_id"], "home_team": row["home_team"], "away_team": row["away_team"],
            "kickoff_utc": row["kickoff_utc"], "matchweek": int(row["matchweek"]), "group": row["group"],
            "status": row["status"], "actual_score": actual_score,
            "market_available": bool(row["market_available"]),
            **c,
        })
    candidates = pd.DataFrame(rows)

    weeks_out = []
    for week_start, group in candidates.groupby("week_start", sort=True):
        ranked = group.sort_values("edge", ascending=False).head(TOP_N_PER_WEEK)
        picks = []
        for rank, (_, r) in enumerate(ranked.iterrows(), start=1):
            picks.append({
                "rank": rank, "match_id": r["match_id"], "home_team": r["home_team"], "away_team": r["away_team"],
                "kickoff_utc": r["kickoff_utc"].isoformat(), "matchweek": r["matchweek"], "group": r["group"],
                "status": r["status"], "market": "moneyline", "pick": r["pick"],
                "probability": r["probability"], "edge": r["edge"],
                "outcome": r["outcome"] if pd.notna(r["outcome"]) else None,
                "actual_score": r["actual_score"] if pd.notna(r["actual_score"]) else None,
                "market_available": bool(r["market_available"]),
            })
        weeks_out.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "picks": picks,
        })
    weeks_out.sort(key=lambda w: w["week_start"])

    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "ranking_method": (
            "edge over baseline (moneyline pick probability minus 1/3) -- moneyline only, this "
            "competition's one real-backtested market; see module docstring for why BTTS/spread/totals "
            "are excluded here unlike the domestic Trusted Picks table."
        ),
        "weeks": weeks_out,
    }
    _write(payload)


if __name__ == "__main__":
    build_international_trusted_picks()
