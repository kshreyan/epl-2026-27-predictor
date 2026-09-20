"""Transforms existing CSV outputs into dashboard-ready JSON (spec
section 30, plus one addition for the site's model-performance view).
This is a pure data-shape transform -- it does not compute anything
new (with the minor exception of joining a few small CSVs together in
`build_model_performance_json`), so it is safe to run any time after
the prediction, simulation, backtest, and calibration pipelines have
produced their CSV outputs.

`{league}_weekly_changes.json` has no real content to transform until
a matchweek has been played. `{league}_model_market_disagreements.json`
is real once at least one fixture has real market odds (see
build_model_market_disagreements_json below) -- both are written with
an empty `data` array and an explicit `status`/`note` when there is
nothing real yet, so dashboard code can be built against the final
schema now and simply start receiving real rows once real data exists.

Every output file is prefixed by league_id (EPL keeps its exact
original filenames, e.g. `epl_expected_table.json`, since `league_id`
"epl" produces byte-identical names to what this project had before
multi-league support existed). Every envelope also now carries a real
`"league"` field (league_id) so the site never has to infer which
competition a JSON file belongs to from its filename alone.

Run: python -m src.dashboard.build_dashboard_json
(builds every league in config/leagues.yaml; pass --league to build
just one)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import all_league_ids, league_path, load_league_config, single_table_league_ids  # noqa: E402
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


def _envelope(league_id: str, data: list[dict], **extra) -> dict:
    return {
        "league": league_id,
        "generated_at": now_utc_iso(),
        "model_version": MODEL_VERSION,
        "season": "2026-27",
        "record_count": len(data),
        **extra,
        "data": data,
    }


def build_match_predictions_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_match_predictions.csv"))
    records = _to_records(df)
    for r in records:
        for col in ("top_10_scorelines_model_only_json", "top_10_scorelines_market_integrated_json"):
            if isinstance(r.get(col), str) and r[col]:
                try:
                    r[col] = json.loads(r[col])
                except json.JSONDecodeError:
                    pass
    _write_json(league_path(league_id, "match_predictions.json"), _envelope(league_id, records))


def build_expected_table_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_expected_table.csv")).sort_values("expected_position")
    _write_json(league_path(league_id, "expected_table.json"), _envelope(league_id, _to_records(df)))


def build_position_distribution_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_position_distribution.csv"))
    _write_json(league_path(league_id, "position_distribution.json"), _envelope(league_id, _to_records(df)))


def build_title_race_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_title_race.csv"))
    _write_json(league_path(league_id, "title_race.json"), _envelope(league_id, _to_records(df)))


def build_top4_race_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_top4_probabilities.csv"))
    _write_json(league_path(league_id, "top4_race.json"), _envelope(league_id, _to_records(df)))


def build_relegation_race_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_relegation_probabilities.csv"))
    _write_json(league_path(league_id, "relegation_race.json"), _envelope(league_id, _to_records(df)))


def build_match_explanations_json(league_id: str) -> None:
    df = pd.read_csv(OUT_DIR / league_path(league_id, "2026_27_match_explanations.csv"))
    _write_json(league_path(league_id, "match_explanations.json"), _envelope(league_id, _to_records(df)))


def build_model_market_disagreements_json(league_id: str) -> None:
    """Real once real market odds exist for at least one fixture (which,
    before kickoff, is only ever a handful -- bookmakers post markets
    shortly before their own kickoff). Compares the model's own raw
    (uncalibrated) Dixon-Coles probability against the real de-vigged
    market probability from the prediction ledger's latest pre-kickoff
    row per fixture -- the raw probability, not the published (possibly
    market-blended) one, since the point here is to show how much the
    model and market actually disagree, not a figure that's already
    been pulled toward market by the blend."""
    out_name = league_path(league_id, "model_market_disagreements.json")
    ledger_path = OUT_DIR / league_path(league_id, "2026_27_prediction_ledger.csv")
    if not ledger_path.exists():
        _write_json(out_name, _envelope(
            league_id, [], status="not_yet_available",
            note="No prediction ledger exists yet -- run src/models/predict_all_matches.py first.",
        ))
        return

    from src.evaluation.prediction_ledger import read_ledger, select_pre_kickoff_predictions

    ledger = read_ledger(ledger_path)
    if ledger.empty:
        _write_json(out_name, _envelope(
            league_id, [], status="not_yet_available", note="Prediction ledger is empty.",
        ))
        return

    selected = select_pre_kickoff_predictions(ledger)
    with_market = selected[selected["market_available"] == True]  # noqa: E712
    if with_market.empty:
        _write_json(out_name, _envelope(
            league_id, [], status="not_yet_available",
            note="No live odds feed is configured yet, or no fixture currently has a real market posted "
                 "(bookmakers only post markets shortly before kickoff) -- every 2026-27 prediction "
                 "is model-only for now.",
        ))
        return

    rows = []
    for _, r in with_market.iterrows():
        disagreement = max(
            abs(r["dc_raw_home_win_prob"] - r["market_home_win_prob"]),
            abs(r["dc_raw_draw_prob"] - r["market_draw_prob"]),
            abs(r["dc_raw_away_win_prob"] - r["market_away_win_prob"]),
        )
        rows.append({
            "match_id": r["match_id"], "home_team": r["home_team"], "away_team": r["away_team"],
            "model_home_win_prob": round(float(r["dc_raw_home_win_prob"]), 4),
            "model_draw_prob": round(float(r["dc_raw_draw_prob"]), 4),
            "model_away_win_prob": round(float(r["dc_raw_away_win_prob"]), 4),
            "market_home_win_prob": round(float(r["market_home_win_prob"]), 4),
            "market_draw_prob": round(float(r["market_draw_prob"]), 4),
            "market_away_win_prob": round(float(r["market_away_win_prob"]), 4),
            "max_class_disagreement": round(float(disagreement), 4),
        })
    rows.sort(key=lambda x: x["max_class_disagreement"], reverse=True)

    _write_json(out_name, _envelope(
        league_id, rows, status="real",
        note="model_* is the raw (uncalibrated) Dixon-Coles probability; market_* is the real, "
             "de-vigged market-consensus probability. Sorted by max_class_disagreement descending.",
    ))


def build_weekly_changes_json(league_id: str) -> None:
    out_name = league_path(league_id, "weekly_changes.json")
    probability_changes_glob = sorted((OUT_DIR / "weekly").glob(f"{league_id}_matchweek_*_probability_changes.csv"))
    if not probability_changes_glob:
        _write_json(out_name, _envelope(
            league_id, [], status="not_yet_available",
            note="No matchweek has concluded yet for this league, so there is no week-over-week "
                 "probability change to report.",
        ))
        return
    latest = probability_changes_glob[-1]
    df = pd.read_csv(latest)
    _write_json(out_name, _envelope(league_id, _to_records(df), status="real", source_file=latest.name))


def build_model_performance_json(league_id: str) -> None:
    """Backtest model comparison + calibration reliability + the paired-
    bootstrap ensemble-vs-Dixon-Coles significance result, combined for
    the dashboard's model-performance/calibration view."""
    out_name = league_path(league_id, "model_performance.json")
    comparison_path = OUT_DIR / league_path(league_id, "backtest_model_comparison.csv")
    if not comparison_path.exists():
        _write_json(out_name, _envelope(
            league_id, [], status="not_yet_available",
            note="No backtest has been run yet for this league -- run src/evaluation/backtest.py first.",
        ))
        return
    comparison = pd.read_csv(comparison_path)
    reliability_path = OUT_DIR / league_path(league_id, "2026_27_reliability_tables.csv")
    reliability = pd.read_csv(reliability_path) if reliability_path.exists() else pd.DataFrame()
    summary_path = OUT_DIR / league_path(league_id, "2026_27_calibration_summary.csv")
    calibration_summary = _to_records(pd.read_csv(summary_path))[0] if summary_path.exists() else None
    ensemble_per_season_path = OUT_DIR / league_path(league_id, "ensemble_per_season_comparison.csv")
    ensemble_per_season = _to_records(pd.read_csv(ensemble_per_season_path)) if ensemble_per_season_path.exists() else []

    payload = _envelope(
        league_id, _to_records(comparison),
        reliability_table=_to_records(reliability),
        calibration_summary=calibration_summary,
        ensemble_per_season_comparison=ensemble_per_season,
    )
    _write_json(out_name, payload)


def build_leagues_manifest() -> None:
    """A small manifest of every active league (id + display name +
    format) so the site never has to hardcode a league list -- adding a
    new league to config/leagues.yaml is enough for it to appear in the
    site's competition switcher, no frontend code change needed. Every
    league (all_league_ids(), not just single_table_league_ids()) is
    included -- a "groups" competition (e.g. UEFA Nations League) has
    no table/races/season-simulation tabs, but it does have its own
    section the switcher should still be able to reach; the `format`
    field is how the frontend knows which nav tabs/default route apply
    to a given entry."""
    leagues = [
        {
            "league_id": lid, "display_name": load_league_config(lid).display_name,
            "country": load_league_config(lid).country, "format": load_league_config(lid).format,
        }
        for lid in all_league_ids()
    ]
    _write_json("leagues.json", {"generated_at": now_utc_iso(), "leagues": leagues})


def build_all_for_league(league_id: str) -> None:
    build_match_predictions_json(league_id)
    build_expected_table_json(league_id)
    build_position_distribution_json(league_id)
    build_title_race_json(league_id)
    build_top4_race_json(league_id)
    build_relegation_race_json(league_id)
    build_match_explanations_json(league_id)
    build_model_market_disagreements_json(league_id)
    build_weekly_changes_json(league_id)
    build_model_performance_json(league_id)


def main(league_id: str | None = None) -> None:
    league_ids = [league_id] if league_id else single_table_league_ids()
    for lid in league_ids:
        print(f"--- Building dashboard JSON for {lid} ---")
        try:
            build_all_for_league(lid)
        except FileNotFoundError as e:
            # One league mid-bootstrap (a required CSV genuinely doesn't
            # exist yet) must never take down every other league's real,
            # already-working dashboard rebuild -- print and move on,
            # don't silently swallow it either.
            print(f"WARNING: skipping {lid}'s dashboard JSON -- {e}")
    build_leagues_manifest()

    from src.dashboard.build_trusted_picks_json import build_trusted_picks
    build_trusted_picks()

    # Nations League has its own, separately-built match-predictions and
    # trusted-picks JSON (see src/dashboard/build_nations_league_
    # dashboard_json.py / build_international_trusted_picks_json.py) --
    # a "groups" competition, not part of the single_table loop above.
    # Rebuilding here keeps it current on every full pipeline/weekly-
    # automation run; both no-op safely (an empty, explicitly-flagged
    # payload) if predict_nations_league_matches.py hasn't run yet.
    from src.dashboard.build_nations_league_dashboard_json import build_nations_league_dashboard_json
    from src.dashboard.build_international_trusted_picks_json import build_international_trusted_picks
    build_nations_league_dashboard_json()
    build_international_trusted_picks()


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default=None, dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
