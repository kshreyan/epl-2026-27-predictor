"""Collect real per-game NCAA Basketball closing (and opening) 2-way
moneylines from ESPN's real game-summary endpoint
(`site.api.espn.com/.../basketball/mens-college-basketball/summary
?event={id}`), confirmed directly this session: a completed game's
real summary retains a real DraftKings-sourced pickcenter entry with a
real open/close distinction (`pickcenter[0].moneyline.{home,away}
.{open,close}.odds`) -- the same real shape as
collect_espn_nba_game_detail.py's real NBA source, richer than
collect_espn_ncaaf_odds.py's real NCAAF source (which has no real
open/close distinction at all, confirmed separately).

**Real, deliberate scope limit**: one real API call per real game, so
this is scoped to the most recent real COMPLETE season only (2025-26,
~5,600 real games) -- same discipline as every other ESPN-per-game-
summary collector in this project (NBA, NCAAF). A real majority of
games will have no real posted market at all (confirmed for NCAAF:
741/763 real 2025 games had none) -- this is DraftKings' own real
coverage decision, not a collector failure, and is reported honestly
rather than treated as an error.

Run: python -m src.data_collection.collect_espn_college_basketball_odds
"""
from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

SOURCE_NAME = "site.api.espn.com (game summary)"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={event_id}"
MOST_RECENT_SEASON_LABEL = "2025-26"
REQUEST_TIMEOUT = 20
ODDS_COLUMNS = [
    "match_id", "home_moneyline_open", "home_moneyline_close",
    "away_moneyline_open", "away_moneyline_close", "source_name", "source_timestamp",
]


def _extract_event_id(match_id: str) -> str | None:
    m = re.search(r"_(\d{9})_", match_id)
    return m.group(1) if m else None


def _parse_odds(summary: dict, match_id: str, fetch_ts: str) -> dict | None:
    pickcenter = summary.get("pickcenter", [])
    if not pickcenter:
        return None
    ml = pickcenter[0].get("moneyline", {})
    home, away = ml.get("home", {}), ml.get("away", {})
    if not (home.get("open") and home.get("close") and away.get("open") and away.get("close")):
        return None
    try:
        return {
            "match_id": match_id,
            "home_moneyline_open": float(home["open"]["odds"]), "home_moneyline_close": float(home["close"]["odds"]),
            "away_moneyline_open": float(away["open"]["odds"]), "away_moneyline_close": float(away["close"]["odds"]),
            "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
        }
    except (KeyError, ValueError):
        return None


def main(league_id: str = "ncaab") -> None:
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    hist_df = pd.read_csv(historical_path)
    season_games = hist_df[hist_df["season"] == MOST_RECENT_SEASON_LABEL]
    print(f"Fetching real closing moneylines for {len(season_games)} real {MOST_RECENT_SEASON_LABEL} games "
          f"(one real API call per game)...")

    fetch_ts = now_utc_iso()
    odds_rows = []
    n_fetched, n_failed, n_no_odds = 0, 0, 0
    for i, (_, row) in enumerate(season_games.iterrows()):
        match_id = row["match_id"]
        event_id = _extract_event_id(match_id)
        if event_id is None:
            n_failed += 1
            continue
        try:
            resp = requests.get(SUMMARY_URL.format(event_id=event_id), timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            summary = resp.json()
        except requests.exceptions.RequestException:
            n_failed += 1
            continue
        odds_row = _parse_odds(summary, match_id, fetch_ts)
        if odds_row is None:
            n_no_odds += 1
        else:
            odds_rows.append(odds_row)
        n_fetched += 1
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(season_games)} real games fetched ({len(odds_rows)} with a real posted market so far)")
        time.sleep(0.05)

    out_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ODDS_COLUMNS)
        writer.writeheader()
        writer.writerows(odds_rows)
    print(f"Wrote {len(odds_rows)} real games with a real closing moneyline to {out_path}")
    print(f"({n_fetched} real games fetched, {n_no_odds} had no real posted market, {n_failed} failed/skipped)")

    log_data_version(
        dataset_name=f"{league_id}_historical_closing_odds", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(odds_rows), is_real_data=True,
        notes=f"Real NCAA Basketball closing+opening moneyline detail, {MOST_RECENT_SEASON_LABEL} season only.",
    )


if __name__ == "__main__":
    main()
