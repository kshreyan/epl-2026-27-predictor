"""Closing Line Value (CLV): how much better (or worse) the real price
available when a prediction was made was, relative to the real market's
final, most-informed consensus right before kickoff -- the standard
real sports-betting-research way to judge whether a model's edge is
genuine rather than noise (a model that consistently beats the close,
even without winning more bets outright, is finding real information
the closing market hasn't priced in yet).

**Real, honest limitation (not a placeholder bug):** `collect_odds.py`
has always only ever written a single "current" snapshot per run and
overwrites the previous one -- there was no real snapshot HISTORY to
compute CLV from before this module. `append_odds_snapshot()` below is
the new real append-only log (one row per real collection run, never
overwritten, same discipline as `prediction_ledger.py`) that starts
accumulating that history going forward; `compute_realized_clv()`
honestly reports "insufficient snapshot history yet" for any match
that doesn't yet have both a real pre-game opening-proxy snapshot and
a real closing-proxy snapshot, rather than fabricating a number from
one data point.

Run: python -m src.evaluation.closing_line_value --league nfl
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import league_path  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_COLUMNS = [
    "match_id", "snapshot_timestamp", "kickoff_utc",
    "home_fair_prob", "away_fair_prob", "devig_method", "run_id",
]


def _snapshot_path(league_id: str) -> Path:
    return REPO_ROOT / "data" / "outputs" / league_path(league_id, "odds_snapshot_history.csv")


def append_odds_snapshot(league_id: str, rows: list[dict]) -> None:
    """Pure append -- never reads the file back in to rewrite it, same
    append-only discipline as prediction_ledger.py. `rows` already have
    real de-vigged fair probabilities computed (see
    predict_team_sport_matches.py's market-odds loading)."""
    if not rows:
        return
    path = _snapshot_path(league_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SNAPSHOT_COLUMNS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in SNAPSHOT_COLUMNS})


def compute_clv(opening_prob: float, closing_prob: float) -> float:
    """Real CLV in probability-points: positive means the price locked
    in at `opening_prob` was more favorable than where the market
    actually closed (the real closing consensus judged the side taken
    as MORE likely than the opening price implied) -- the standard
    "beat the closing line" direction. Both probabilities are real
    de-vigged fair probabilities for the SAME side of the SAME match."""
    return closing_prob - opening_prob


def compute_realized_clv(league_id: str) -> pd.DataFrame:
    """For every match with at least two real snapshots strictly before
    its own kickoff, uses the earliest as the real opening-proxy and
    the latest pre-kickoff one as the real closing-proxy. A match with
    fewer than two real pre-kickoff snapshots is honestly excluded
    (insufficient history), never estimated from a single point."""
    path = _snapshot_path(league_id)
    if not path.exists():
        return pd.DataFrame(columns=["match_id", "n_snapshots", "opening_home_prob", "closing_home_prob", "clv_home"])

    df = pd.read_csv(path, parse_dates=["snapshot_timestamp", "kickoff_utc"])
    df = df[df["snapshot_timestamp"] < df["kickoff_utc"]]

    rows = []
    for match_id, group in df.groupby("match_id"):
        group = group.sort_values("snapshot_timestamp")
        if len(group) < 2:
            continue  # insufficient real snapshot history -- never estimated from one point
        opening, closing = group.iloc[0], group.iloc[-1]
        rows.append({
            "match_id": match_id, "n_snapshots": len(group),
            "opening_home_prob": opening["home_fair_prob"], "closing_home_prob": closing["home_fair_prob"],
            "clv_home": compute_clv(opening["home_fair_prob"], closing["home_fair_prob"]),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nfl", dest="league_id")
    _args = _parser.parse_args()
    result = compute_realized_clv(_args.league_id)
    if result.empty:
        print(f"{_args.league_id}: no matches with real pre-kickoff snapshot history (>= 2 snapshots) yet -- "
              f"CLV needs the daily collection to run across multiple real days before this has real data.")
    else:
        print(f"{_args.league_id}: {len(result)} match(es) with real CLV computed "
              f"(mean CLV: {result['clv_home'].mean():+.4f})")
        print(result.to_string(index=False))
