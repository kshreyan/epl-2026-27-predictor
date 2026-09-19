"""Builds data/outputs/dashboard/trusted_picks.json: a cross-league,
cross-market "most trusted predictions" table, one per calendar week.

Pools every league's moneyline, BTTS, spread, and totals picks together
and ranks them by **edge over baseline** -- predicted probability minus
that market's naive baseline (1/3 for a 3-way moneyline pick, 1/2 for
the three binary markets) -- not raw probability. Ranking by raw
probability would systematically favor the binary markets, which sit
above 50% far more often than a 3-way moneyline pick without actually
reflecting a more confident call; edge-over-baseline is comparable
across market types.

Weeks are real calendar weeks (Monday-start, by each match's own real
kickoff date) spanning every league at once -- not each league's own
internal matchweek numbering, which drifts out of sync across leagues
with different season-start dates.

Only weeks that have already started, plus the single next upcoming
week, are included -- deliberately not the whole remaining season.
Every fixture already has a prediction (the full-season predict run),
but a "trusted pick" for a match dozens of weeks out would just be
today's fixed team-strength ratings restated with no real forward-
looking meaning; that week gets its own honest picks once it's
actually reached.

Run: python -m src.dashboard.build_trusted_picks_json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import all_league_ids, load_league_config  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "outputs"
DASHBOARD_DIR = OUT_DIR / "dashboard"

TOP_N_PER_WEEK = 15
MONEYLINE_BASELINE = 1.0 / 3.0
BINARY_BASELINE = 0.5


def _week_start(kickoff_utc: pd.Timestamp) -> pd.Timestamp:
    """Monday of the ISO calendar week containing this kickoff."""
    return (kickoff_utc - pd.Timedelta(days=kickoff_utc.weekday())).normalize()


def _moneyline_candidate(row: pd.Series) -> dict:
    probs = {
        "home": row["home_win_prob_model_only"], "draw": row["draw_prob_model_only"],
        "away": row["away_win_prob_model_only"],
    }
    side = max(probs, key=probs.get)
    probability = probs[side]
    outcome = None
    if row["status"] == "completed":
        actual_side = {"home_win": "home", "draw": "draw", "away_win": "away"}[row["actual_result"]]
        outcome = "win" if side == actual_side else "loss"
    return {
        "market": "moneyline", "pick": row["moneyline_pick"],
        "probability": round(float(probability), 4), "edge": round(float(probability) - MONEYLINE_BASELINE, 4),
        "outcome": outcome,
    }


def _btts_candidate(row: pd.Series) -> dict:
    probability = max(row["btts_yes_prob_model_only"], row["btts_no_prob_model_only"])
    side = "yes" if row["btts_yes_prob_model_only"] >= 0.5 else "no"
    outcome = None
    if row["status"] == "completed":
        actual = "yes" if (row["actual_home_goals"] > 0 and row["actual_away_goals"] > 0) else "no"
        outcome = "win" if side == actual else "loss"
    return {
        "market": "btts", "pick": row["btts_pick"],
        "probability": round(float(probability), 4), "edge": round(float(probability) - BINARY_BASELINE, 4),
        "outcome": outcome,
    }


def _totals_candidate(row: pd.Series) -> dict:
    probability = max(row["over_prob_model_only"], row["under_prob_model_only"])
    side = "over" if row["over_prob_model_only"] >= 0.5 else "under"
    outcome = None
    if row["status"] == "completed":
        actual_total = row["actual_home_goals"] + row["actual_away_goals"]
        line = row["total_goals_line_model_only"]
        if actual_total == line:
            outcome = "push"
        else:
            actual = "over" if actual_total > line else "under"
            outcome = "win" if side == actual else "loss"
    return {
        "market": "totals", "pick": row["totals_pick"],
        "probability": round(float(probability), 4), "edge": round(float(probability) - BINARY_BASELINE, 4),
        "outcome": outcome,
    }


def _spread_candidate(row: pd.Series) -> dict:
    probability = max(row["home_cover_prob_model_only"], row["away_cover_prob_model_only"])
    side = "home" if row["home_cover_prob_model_only"] >= 0.5 else "away"
    outcome = None
    if row["status"] == "completed":
        diff = row["actual_home_goals"] - row["actual_away_goals"] + row["handicap_line_model_only"]
        if abs(diff) < 1e-9:
            outcome = "push"
        else:
            actual = "home" if diff > 0 else "away"
            outcome = "win" if side == actual else "loss"
    return {
        "market": "spread", "pick": row["spread_pick"],
        "probability": round(float(probability), 4), "edge": round(float(probability) - BINARY_BASELINE, 4),
        "outcome": outcome,
    }


CANDIDATE_BUILDERS = [_moneyline_candidate, _btts_candidate, _totals_candidate, _spread_candidate]


def _load_all_candidates() -> pd.DataFrame:
    rows = []
    for league_id in all_league_ids():
        league_cfg = load_league_config(league_id)
        pred_path = OUT_DIR / f"{league_id}_2026_27_match_predictions.csv"
        if not pred_path.exists():
            continue
        df = pd.read_csv(pred_path)
        df["kickoff_utc"] = pd.to_datetime(df["kickoff_utc"], utc=True)
        for _, row in df.iterrows():
            week_start = _week_start(row["kickoff_utc"])
            for build in CANDIDATE_BUILDERS:
                c = build(row)
                rows.append({
                    "week_start": week_start,
                    "league": league_id, "league_display_name": league_cfg.display_name,
                    "match_id": row["match_id"], "home_team": row["home_team"], "away_team": row["away_team"],
                    "kickoff_utc": row["kickoff_utc"], "matchweek": int(row["matchweek"]), "status": row["status"],
                    "actual_score": (
                        f"{int(row['actual_home_goals'])}-{int(row['actual_away_goals'])}"
                        if row["status"] == "completed" else None
                    ),
                    **c,
                })
    return pd.DataFrame(rows)


def build_trusted_picks() -> None:
    candidates = _load_all_candidates()
    if candidates.empty:
        DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_DIR / "trusted_picks.json", "w") as f:
            json.dump({"generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "weeks": []}, f, indent=2)
        print("Wrote trusted_picks.json (0 weeks -- no league has predictions yet)")
        return

    now = pd.Timestamp.now(tz=timezone.utc)
    horizon = _week_start(now) + pd.Timedelta(days=7)
    in_scope = candidates[candidates["week_start"] <= horizon].copy()

    weeks_out = []
    for week_start, group in in_scope.groupby("week_start", sort=True):
        ranked = group.sort_values("edge", ascending=False).head(TOP_N_PER_WEEK)
        picks = []
        for rank, (_, r) in enumerate(ranked.iterrows(), start=1):
            # pandas' string dtype uses NaN as its null sentinel even for
            # a column built from plain Python `None`s -- convert back to
            # real None here so json.dump (allow_nan=False) emits `null`
            # instead of raising on a float NaN it refuses to serialize.
            outcome = r["outcome"] if pd.notna(r["outcome"]) else None
            actual_score = r["actual_score"] if pd.notna(r["actual_score"]) else None
            picks.append({
                "rank": rank,
                "league": r["league"], "league_display_name": r["league_display_name"],
                "match_id": r["match_id"], "home_team": r["home_team"], "away_team": r["away_team"],
                "kickoff_utc": r["kickoff_utc"].isoformat(),
                "matchweek": r["matchweek"], "status": r["status"],
                "market": r["market"], "pick": r["pick"],
                "probability": r["probability"], "edge": r["edge"],
                "outcome": outcome, "actual_score": actual_score,
            })
        weeks_out.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "picks": picks,
        })
    weeks_out.sort(key=lambda w: w["week_start"], reverse=True)

    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "ranking_method": (
            "edge over baseline (pick probability minus 1/3 for moneyline, 1/2 for BTTS/spread/totals), "
            f"top {TOP_N_PER_WEEK} per week pooled across every league and market"
        ),
        "weeks": weeks_out,
    }
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_DIR / "trusted_picks.json", "w") as f:
        json.dump(payload, f, indent=2, default=str, allow_nan=False)
    print(f"Wrote trusted_picks.json ({len(weeks_out)} week(s))")


if __name__ == "__main__":
    build_trusted_picks()
