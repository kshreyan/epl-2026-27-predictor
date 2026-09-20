"""Builds data/outputs/dashboard/nations_league_match_predictions.json.

Not part of build_dashboard_json.py's build_all_for_league: that
builds a table, position distribution, and title/top4/relegation race
from a season simulation, none of which exist (or make sense) for a
"groups" competition with no combined table (see src/leagues.py
LeagueConfig.format) -- this builds only what Nations League actually
has, real match-level predictions.

Run: python -m src.dashboard.build_nations_league_dashboard_json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.dashboard.build_dashboard_json import _to_records, _write_json  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

LEAGUE_ID = "nations_league"
OUT_DIR = REPO_ROOT / "data" / "outputs"
PREDICTIONS_PATH = OUT_DIR / "nations_league_2026_27_match_predictions.csv"


def build_nations_league_dashboard_json() -> None:
    if not PREDICTIONS_PATH.exists():
        _write_json("nations_league_match_predictions.json", {
            "league": LEAGUE_ID, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
            "season": "2026-27", "record_count": 0, "data": [],
            "status": "not_yet_available",
            "note": "No predictions yet -- run predict_nations_league_matches.py first.",
        })
        return

    df = pd.read_csv(PREDICTIONS_PATH)
    records = _to_records(df)
    for r in records:
        if isinstance(r.get("top_10_scorelines_json"), str) and r["top_10_scorelines_json"]:
            try:
                r["top_10_scorelines_json"] = json.loads(r["top_10_scorelines_json"])
            except json.JSONDecodeError:
                pass

    payload = {
        "league": LEAGUE_ID, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "season": "2026-27", "record_count": len(records),
        "moneyline_model_note": (
            "Elo-only, real-backtested (see reports/nations_league_model_selection_report.md). "
            "BTTS/spread/totals are Simple-Poisson-derived and less validated -- see each row's own "
            "moneyline_model_source / derived_markets_model_source fields."
        ),
        "data": records,
    }
    _write_json("nations_league_match_predictions.json", payload)


if __name__ == "__main__":
    build_nations_league_dashboard_json()
