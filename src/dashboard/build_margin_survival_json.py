"""Builds the +2 Margin Survival dashboard JSON: one per-league file
(data/outputs/dashboard/{league}_margin_survival.json, EVERY team in
EVERY match -- no eligibility filter) plus a combined cross-league
leaderboard (top20_margin_survival.json) of the best real PICK +2 /
LEAN +2 candidates.

Covers the 5 domestic leagues with a real, backtested, PRIMARY Dixon-
Coles fit (see src/models/compute_margin_survival.py's module
docstring) plus UCL/UEL/UECL (see compute_margin_survival_continental.py's
module docstring) -- built on request even though those three
competitions' own real backtest found Dixon-Coles clearly weaker than
Elo, their actual moneyline model; every row for those three says so
plainly in engine_note/why_text. Every row carries a `verdict` (PICK
+2 / LEAN +2 / PASS) that combines absolute blowout risk with real
market price where one exists -- most fixtures have no real market
posted yet (bookmakers only post close to kickoff), so most verdicts
are risk-tier only; `real_line`/`real_odds`/`value_gap` are null
rather than estimated whenever no real market exists for that
fixture.

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

# UCL/UEL/UECL (see compute_margin_survival_continental.py's module
# docstring): built on request despite the real backtest finding Elo
# clearly beats Dixon-Coles for all three competitions' own moneyline
# prediction -- unlike the 5 domestic leagues above, the Dixon-Coles
# surface this reads from is NOT this league's primary/best-validated
# model, just the weaker of two real models tested. engine_note below
# is written per-league so this distinction is never glossed over.
CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS = ["ucl", "uel", "uecl"]


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
    df["data_confidence"] = df.apply(_confidence, axis=1)

    tally = df["verdict"].value_counts().to_dict()
    if league_id in CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS:
        engine_note = (
            "Every team in every match, every round: P_cover/P_push/P_fail read directly off this "
            "competition's own separately-fit Dixon-Coles score matrix -- NOT the same model as this "
            f"competition's moneyline prediction, which is Elo-only (the real backtest found Elo clearly "
            f"beats Dixon-Coles here -- see reports/{league_id}_model_selection_report.md). Treat these "
            "verdicts with real caution. Each row's verdict (PICK +2 / LEAN +2 / PASS) gates on absolute "
            "blowout risk first, then breaks ties with real market price where one currently exists."
        )
    else:
        engine_note = (
            "Every team in every match, every gameweek: P_cover/P_push/P_fail read directly off the same "
            "backtested Dixon-Coles score matrix used for this league's own moneyline predictions -- "
            "not a separate multi-model ensemble. Each row's verdict (PICK +2 / LEAN +2 / PASS) gates on "
            "absolute blowout risk first, then breaks ties with real market price where one currently exists "
            "(most fixtures have none yet -- bookmakers only post close to kickoff)."
        )
    payload = {
        "league": league_id, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "season": "2026-27", "record_count": len(df),
        "verdict_tally": tally,
        "engine_note": engine_note,
        "data": _to_records(df),
    }
    _write_json(f"{league_id}_margin_survival.json", payload)
    return df


_VERDICT_RANK = {"PICK +2": 0, "LEAN +2": 1, "PASS": 2}


def build_top20(all_leagues: dict[str, pd.DataFrame]) -> None:
    frames = []
    for league_id, df in all_leagues.items():
        if df.empty:
            continue
        upcoming = df[df["status"] != "completed"].copy()
        upcoming["league_display_name"] = load_league_config(league_id).display_name
        frames.append(upcoming)

    if not frames:
        _write_json("top20_margin_survival.json", {
            "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
            "view": "best_verdict", "record_count": 0, "data": [],
            "note": "No upcoming fixtures across the covered leagues yet.",
        })
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["verdict"] != "PASS"].copy()
    combined["verdict_rank"] = combined["verdict"].map(_VERDICT_RANK)
    # Within a verdict tier, real price value breaks ties (best value first);
    # rows with no real market (value_gap null) sort after ones that do,
    # then by lowest p_fail -- never let "no price to compare" outrank a
    # fixture that actually has one.
    combined["has_value_gap"] = combined["value_gap"].notna()
    combined = combined.sort_values(
        by=["verdict_rank", "has_value_gap", "value_gap", "p_fail"],
        ascending=[True, False, False, True],
    ).head(TOP20_SIZE).reset_index(drop=True)
    combined = combined.drop(columns=["verdict_rank", "has_value_gap"])
    combined.insert(0, "rank", combined.index + 1)

    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
        "view": "best_verdict",
        "note": (
            "Ranked by verdict first (Pick +2 before Lean +2 -- Pass is excluded here), then by real price "
            "value where a real market exists, then by lowest blowout risk. The verdict pill on each row "
            "already synthesizes risk and price -- this is not a separate signal, and still not advice."
        ),
        "record_count": len(combined),
        "data": _to_records(combined),
    }
    _write_json("top20_margin_survival.json", payload)


def main() -> None:
    all_leagues = {
        lid: build_league_margin_survival_json(lid)
        for lid in MARGIN_SURVIVAL_LEAGUE_IDS + CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS
    }
    build_top20(all_leagues)


if __name__ == "__main__":
    main()
