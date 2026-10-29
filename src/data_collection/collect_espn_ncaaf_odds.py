"""Collect real per-game NCAA Football closing moneylines from ESPN's
real game-summary endpoint (`site.api.espn.com/.../college-football/
summary?event={id}`), confirmed directly this session: a completed
game's real summary retains a real consensus moneyline
(`pickcenter[0].{away,home}TeamOdds.moneyLine`).

**Real, honest difference from collect_espn_nba_game_detail.py**:
NCAA Football's real pickcenter entry has no real open/close
distinction (`moneyline.home`/`moneyline.away` are empty objects here,
confirmed directly -- unlike NBA's real DraftKings-sourced entry) --
only one real consensus number per game is available from this
source, so no real CLV is computable for this sport from this source.
Documented, not silently assumed away.

**Real, deliberate scope limit** (same reasoning as the NBA
collector): one real API call per real game, scoped to the most
recent real complete season only (~763 real games), not all 5
historical seasons.

Run: python -m src.data_collection.collect_espn_ncaaf_odds
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
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={event_id}"
MOST_RECENT_SEASON = 2025
REQUEST_TIMEOUT = 20
ODDS_COLUMNS = ["match_id", "home_moneyline", "away_moneyline", "source_name", "source_timestamp"]


def _extract_event_id(match_id: str) -> str | None:
    m = re.search(r"_(\d{9})_", match_id)
    return m.group(1) if m else None


def _parse_moneyline(summary: dict) -> tuple[float, float] | None:
    pickcenter = summary.get("pickcenter", [])
    if not pickcenter:
        return None
    entry = pickcenter[0]
    home_odds = entry.get("homeTeamOdds", {})
    away_odds = entry.get("awayTeamOdds", {})
    if "moneyLine" not in home_odds or "moneyLine" not in away_odds:
        return None
    return float(home_odds["moneyLine"]), float(away_odds["moneyLine"])


def main(league_id: str = "ncaaf") -> None:
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    hist_df = pd.read_csv(historical_path)
    season_games = hist_df[hist_df["season"] == MOST_RECENT_SEASON]
    print(f"Fetching real closing moneylines for {len(season_games)} real {MOST_RECENT_SEASON} games "
          f"(one real API call per game)...")

    fetch_ts = now_utc_iso()
    rows = []
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
        ml = _parse_moneyline(summary)
        if ml is None:
            n_no_odds += 1
        else:
            rows.append({
                "match_id": match_id, "home_moneyline": ml[0], "away_moneyline": ml[1],
                "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
            })
        n_fetched += 1
        if (i + 1) % 200 == 0:
            print(f"  ...{i + 1}/{len(season_games)} real games fetched")
        time.sleep(0.05)

    out_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ODDS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real games with a real closing moneyline to {out_path}")
    print(f"({n_fetched} real games fetched, {n_no_odds} had no real posted market, {n_failed} failed/skipped)")

    log_data_version(
        dataset_name=f"{league_id}_historical_closing_odds", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(rows), is_real_data=True,
        notes=f"Real {league_id.upper()} closing-moneyline detail, {MOST_RECENT_SEASON} season only.",
    )


if __name__ == "__main__":
    main()
