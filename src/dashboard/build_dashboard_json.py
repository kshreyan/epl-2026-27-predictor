"""Transforms existing CSV outputs into dashboard-ready JSON (spec
section 30, plus one addition for the site's model-performance view).
This is a pure data-shape transform -- it does not compute anything
new (with the minor exception of joining a few small CSVs together in
`build_model_performance_json`), so it is safe to run any time after
the prediction, simulation, backtest, and calibration pipelines have
produced their CSV outputs.

Two of the ten files (`epl_model_market_disagreements.json`,
`epl_weekly_changes.json`) have no real content to transform yet: no
live odds key is configured and no matchweek has been played. Rather
than omit them, each is written with an empty `data` array and an
explicit `status`/`note` explaining why, so dashboard code can be
built against the final schema now and simply start receiving real
rows once real data exists for them.

Run: python -m src.dashboard.build_dashboard_json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "outputs"
DASHBOARD_DIR = OUT_DIR / "dashboard"


def _to_records(df: pd.DataFrame) -> list[dict]:
    """NaN/NaT are not valid JSON tokens (JSON.parse in a browser rejects
    them) -- pandas' default to_dict() leaves them as float('nan'), so
    convert to None first via a JSON round-trip through pandas' own
    NaN-safe serializer rather than hand-rolling per-column null checks."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _write_json(filename: str, payload: dict) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    path = DASHBOARD_DIR / filename
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str, allow_nan=False)
    print(f"Wrote {filename} ({len(payload.get('data', []))} records)")


def _envelope(data: list[dict], **extra) -> dict:
    return {
        "generated_at": now_utc_iso(),
        "model_version": MODEL_VERSION,
        "season": "2026-27",
        "record_count": len(data),
        **extra,
        "data": data,
    }


def build_match_predictions_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_match_predictions.csv")
    records = _to_records(df)
    for r in records:
        for col in ("top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json"):
            if isinstance(r.get(col), str) and r[col]:
                try:
                    r[col] = json.loads(r[col])
                except json.JSONDecodeError:
                    pass
    _write_json("epl_match_predictions.json", _envelope(records))


def build_expected_table_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_expected_table.csv").sort_values("expected_position")
    _write_json("epl_expected_table.json", _envelope(_to_records(df)))


def build_position_distribution_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_position_distribution.csv")
    _write_json("epl_position_distribution.json", _envelope(_to_records(df)))


def build_title_race_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_title_race.csv")
    _write_json("epl_title_race.json", _envelope(_to_records(df)))


def build_top4_race_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_top4_probabilities.csv")
    _write_json("epl_top4_race.json", _envelope(_to_records(df)))


def build_relegation_race_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_relegation_probabilities.csv")
    _write_json("epl_relegation_race.json", _envelope(_to_records(df)))


def build_match_explanations_json() -> None:
    df = pd.read_csv(OUT_DIR / "epl_2026_27_match_explanations.csv")
    _write_json("epl_match_explanations.json", _envelope(_to_records(df)))


def build_model_market_disagreements_json() -> None:
    _write_json("epl_model_market_disagreements.json", _envelope(
        [], status="not_yet_available",
        note="No live odds feed is configured (ODDS_API_KEY unset; the collector is built and tested -- "
             "see src/data_collection/collect_odds.py) -- every 2026-27 prediction is model-only, so "
             "there is no market to disagree with yet.",
    ))


def build_weekly_changes_json() -> None:
    _write_json("epl_weekly_changes.json", _envelope(
        [], status="not_yet_available",
        note="The weekly-update engine exists (src/update_after_matchweek.py) but has never run against "
             "real data: today, 2026-08-18, is before kickoff on 2026-08-21, so there is no completed "
             "matchweek to report changes from yet.",
    ))


def build_model_performance_json() -> None:
    """Backtest model comparison + calibration reliability + the paired-
    bootstrap ensemble-vs-Dixon-Coles significance result, combined for
    the dashboard's model-performance/calibration view."""
    comparison = pd.read_csv(OUT_DIR / "epl_backtest_model_comparison.csv")
    reliability = pd.read_csv(OUT_DIR / "epl_2026_27_reliability_tables.csv")
    summary_path = OUT_DIR / "epl_2026_27_calibration_summary.csv"
    calibration_summary = _to_records(pd.read_csv(summary_path))[0] if summary_path.exists() else None
    ensemble_per_season_path = OUT_DIR / "epl_ensemble_per_season_comparison.csv"
    ensemble_per_season = _to_records(pd.read_csv(ensemble_per_season_path)) if ensemble_per_season_path.exists() else []

    payload = _envelope(
        _to_records(comparison),
        reliability_table=_to_records(reliability),
        calibration_summary=calibration_summary,
        ensemble_per_season_comparison=ensemble_per_season,
    )
    _write_json("epl_model_performance.json", payload)


def main() -> None:
    build_match_predictions_json()
    build_expected_table_json()
    build_position_distribution_json()
    build_title_race_json()
    build_top4_race_json()
    build_relegation_race_json()
    build_match_explanations_json()
    build_model_market_disagreements_json()
    build_weekly_changes_json()
    build_model_performance_json()


if __name__ == "__main__":
    main()
