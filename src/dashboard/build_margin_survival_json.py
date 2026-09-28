"""Builds the +2 Margin Survival dashboard JSON: one per-league file
(data/outputs/dashboard/{league}_margin_survival.json, eligible-team
rows only) plus a combined cross-league leaderboard
(top20_margin_survival.json).

Phase 1 scope (real-data-only, see src/models/compute_margin_survival.py's
module docstring for why): the 5 domestic leagues with a real,
backtested Dixon-Coles fit. The leaderboard ranks purely by lowest
P_fail ("Safest") -- a "Best Value"/"Best Balance" ranking needs real
market +2 Asian Handicap odds, which The Odds API does not reliably
quote at exactly the +2.0 line for most fixtures (checked directly:
EPL's real current spread lines cluster at 0/±0.5/±1/±1.5, a +2.0 line
is rare). That tab is deliberately deferred rather than built on
sparse-to-nonexistent real coverage.

Run: python -m src.dashboard.build_margin_survival_json
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.dashboard.build_dashboard_json import _to_records, _write_json  # noqa: E402
from src.leagues import load_league_config  # noqa: E402
from src.models.compute_margin_survival import MARGIN_SURVIVAL_LEAGUE_IDS  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "outputs"
TOP20_SIZE = 20


def _confidence(row: pd.Series) -> str:
    n_min = min(row["team_history_n_matches"], row["opponent_history_n_matches"])
    if n_min >= 20:
        return "high"
    if n_min >= 10:
        return "moderate"
    return "low"


def build_league_margin_survival_json(league_id: str) -> pd.DataFrame:
    path = OUT_DIR / f"{league_id}_2026_27_margin_survival.csv"
    if not path.exists():
        _write_json(f"{league_id}_margin_survival.json", {
            "league": league_id, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
            "season": "2026-27", "record_count": 0, "data": [],
            "status": "not_yet_available",
            "note": "No margin-survival predictions yet -- run compute_margin_survival.py first.",
        })
        return pd.DataFrame()

    df = pd.read_csv(path)
    eligible = df[df["eligible"]].copy()
    eligible["data_confidence"] = eligible.apply(_confidence, axis=1)

    payload = {
        "league": league_id, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "season": "2026-27", "record_count": len(eligible),
        "engine_note": (
            "Phase 1 (real-data-only): P_cover/P_push/P_fail read directly off the same "
            "backtested Dixon-Coles score matrix used for this league's own moneyline predictions -- "
            "not a separate multi-model ensemble. Ranking by market value (fair vs. market +2 price, EV) "
            "is deferred until real +2.0 Asian Handicap market coverage is reliable."
        ),
        "data": _to_records(eligible),
    }
    _write_json(f"{league_id}_margin_survival.json", payload)
    return eligible


def build_top20(all_eligible: dict[str, pd.DataFrame]) -> None:
    frames = []
    for league_id, df in all_eligible.items():
        if df.empty:
            continue
        upcoming = df[df["status"] != "completed"].copy()
        upcoming["league_display_name"] = load_league_config(league_id).display_name
        frames.append(upcoming)

    if not frames:
        _write_json("top20_margin_survival.json", {
            "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
            "view": "safest", "record_count": 0, "data": [],
            "note": "No eligible upcoming fixtures across the covered leagues yet.",
        })
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("p_fail", ascending=True).head(TOP20_SIZE).reset_index(drop=True)
    combined.insert(0, "rank", combined.index + 1)

    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
        "view": "safest",
        "note": (
            "Phase 1: ranked purely by lowest modeled probability of a 3+ goal defeat (\"Safest\"). "
            "This naturally surfaces heavy favorites with little real betting value at their market price -- "
            "a market-value-aware \"Best Value\"/\"Best Balance\" ranking is planned once reliable real "
            "+2.0 Asian Handicap market coverage exists. See each row's own risk_label and factor scores, "
            "not just its rank, before treating anything here as a recommendation."
        ),
        "record_count": len(combined),
        "data": _to_records(combined),
    }
    _write_json("top20_margin_survival.json", payload)


def main() -> None:
    all_eligible = {lid: build_league_margin_survival_json(lid) for lid in MARGIN_SURVIVAL_LEAGUE_IDS}
    build_top20(all_eligible)


if __name__ == "__main__":
    main()
