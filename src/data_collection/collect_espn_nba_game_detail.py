"""Collect real per-game NBA detail (box-score +/- per player, real
open/close moneyline odds) from ESPN's real game-summary endpoint
(`site.api.espn.com/.../basketball/nba/summary?event={id}`), confirmed
directly this session: a completed game's real summary retains both
its real box score (`boxscore.players[team].statistics[0]`, with a
real "+/-" column per athlete) AND its real moneyline open/close odds
(`pickcenter[0].moneyline.{home,away}.{open,close}.odds`) -- neither
of which collect_espn_schedule.py/collect_espn_historical.py's
lighter schedule-endpoint fetch exposes.

**Real, deliberate scope limit**: one real API call per real game, so
this is scoped to the most recent real COMPLETE season only (not all
5 historical seasons collect_espn_historical.py covers) -- ~1,230 real
calls at ~0.27s/call (confirmed directly this session) is a real,
bounded cost; five seasons' worth would not be. Documented here, not
silently narrowed.

Writes two real outputs:
1. `nba_boxscore_plus_minus.csv` -- one row per real player-game
   (match_id, team, player_name, minutes, plus_minus) for the
   adjusted-plus-minus ridge regression (nba_apm_model.py).
2. `nba_historical_closing_odds.csv` -- one row per real game with a
   real posted moneyline (match_id, home_moneyline_open/close,
   away_moneyline_open/close) for the de-vig/blend backtest and CLV
   (a real per-game open-vs-close pair, unlike Phase 1's NFL/NHL
   sources which needed multiple daily polls to ever have two real
   snapshots to compare).

Run: python -m src.data_collection.collect_espn_nba_game_detail
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
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
MOST_RECENT_SEASON_LABEL = "2025-26"
REQUEST_TIMEOUT = 20

PLUS_MINUS_COLUMNS = ["match_id", "team", "player_name", "minutes", "plus_minus", "source_name", "source_timestamp"]
ODDS_COLUMNS = [
    "match_id", "home_moneyline_open", "home_moneyline_close",
    "away_moneyline_open", "away_moneyline_close", "source_name", "source_timestamp",
]


def _extract_event_id(match_id: str) -> str | None:
    m = re.search(r"_(\d{9})_", match_id)
    return m.group(1) if m else None


def _parse_plus_minus(summary: dict, match_id: str, fetch_ts: str) -> list[dict]:
    rows = []
    boxscore = summary.get("boxscore", {})
    for team_entry in boxscore.get("players", []):
        team_name = team_entry.get("team", {}).get("displayName", "")
        stats_block = team_entry.get("statistics", [{}])[0]
        labels = stats_block.get("labels", [])
        if "+/-" not in labels:
            continue
        pm_idx = labels.index("+/-")
        min_idx = labels.index("MIN") if "MIN" in labels else None
        for athlete in stats_block.get("athletes", []):
            stats = athlete.get("stats", [])
            if len(stats) <= pm_idx or not stats[pm_idx]:
                continue
            try:
                plus_minus = int(stats[pm_idx].replace("+", ""))
            except ValueError:
                continue
            minutes = stats[min_idx] if min_idx is not None and min_idx < len(stats) else ""
            rows.append({
                "match_id": match_id, "team": team_name,
                "player_name": athlete.get("athlete", {}).get("displayName", ""),
                "minutes": minutes, "plus_minus": plus_minus,
                "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
            })
    return rows


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


def main(league_id: str = "nba") -> None:
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    hist_df = pd.read_csv(historical_path)
    season_games = hist_df[hist_df["season"] == MOST_RECENT_SEASON_LABEL]
    print(f"Fetching real per-game detail for {len(season_games)} real {MOST_RECENT_SEASON_LABEL} games "
          f"(one real API call per game)...")

    fetch_ts = now_utc_iso()
    plus_minus_rows, odds_rows = [], []
    n_fetched, n_failed = 0, 0
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
        plus_minus_rows.extend(_parse_plus_minus(summary, match_id, fetch_ts))
        odds_row = _parse_odds(summary, match_id, fetch_ts)
        if odds_row:
            odds_rows.append(odds_row)
        n_fetched += 1
        if (i + 1) % 200 == 0:
            print(f"  ...{i + 1}/{len(season_games)} real games fetched")
        time.sleep(0.05)

    pm_path = REPO_ROOT / "data" / "raw" / "nba_boxscore_plus_minus.csv"
    with open(pm_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PLUS_MINUS_COLUMNS)
        writer.writeheader()
        writer.writerows(plus_minus_rows)
    print(f"Wrote {len(plus_minus_rows)} real player-game +/- rows to {pm_path}")

    odds_path = REPO_ROOT / "data" / "raw" / "nba_historical_closing_odds.csv"
    with open(odds_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ODDS_COLUMNS)
        writer.writeheader()
        writer.writerows(odds_rows)
    print(f"Wrote {len(odds_rows)} real games with real open/close moneyline to {odds_path}")
    print(f"({n_fetched} real games fetched successfully, {n_failed} failed/skipped)")

    log_data_version(
        dataset_name="nba_boxscore_plus_minus", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(plus_minus_rows), is_real_data=True,
        notes=f"Real NBA box-score +/- and closing-odds detail, {MOST_RECENT_SEASON_LABEL} season only.",
    )


if __name__ == "__main__":
    main()
