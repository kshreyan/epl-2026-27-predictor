"""Collect the real current-season NFL/NBA schedule from ESPN's site
API (see espn_api.py for why this source, not fixturedownload.com or
Basketball-Reference). Writes two real outputs from the SAME fetch (no
second pass needed, unlike the continental-cup leagues' separate
fetch_continental_cup_live_results.py -- ESPN's schedule endpoint
already returns real scores inline):

1. `{league}_2026_27_fixtures.csv` -- every real game, `status` always
   "scheduled" (same convention collect_fixtures.py uses for every
   domestic league: a separate ledger carries real results, this file
   is the schedule of record).
2. `{league}_2026_27_real_results.csv` -- real completed games only
   (match_id, home_goals, away_goals, source_name, source_timestamp),
   same shape fetch_continental_cup_live_results.py already produces,
   consumed the same way by predict_team_sport_matches.py.

ESPN's own season-year convention differs by sport and does NOT match
either one uniformly: NFL seasons are labeled by their START year
(e.g. "season=2026" is the real Sept 2026-Feb 2027 season), NBA by
their END year (e.g. "season=2027" is the real Oct 2026-Apr 2027
season) -- confirmed directly, not assumed. ESPN_CURRENT_SEASON below
translates this project's "2026-27" season label to each sport's own
real convention.

No `matchweek` concept exists for NBA (confirmed directly: no `week`
field anywhere in the real schedule data, unlike NFL's real official
week numbers) -- a synthetic calendar-week number (days since the
real season's first game // 7) is used instead, purely for the same
UI pagination `FixturesPage.tsx` already does for every other league;
documented here as synthetic, not an official NBA schedule concept.

Real, honest limitation: ESPN's real game count for a season collected
this early can be lower than the real full-season total (confirmed
directly: an NBA team showed 80 of its real 82 games this far into
the season, the rest presumably still being finalized in ESPN's own
system) -- this collector reports the real count it found rather than
enforcing an exact expected total the way collect_fixtures.py does for
a soccer league's fully-published-in-advance fixture list.

Run: python -m src.data_collection.collect_espn_schedule --league nfl
(also accepts nba)
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_collection.espn_api import fetch_real_season_games  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "site.api.espn.com"
SEASON_LABEL = "2026-27"
ESPN_CURRENT_SEASON = {"nfl": 2026, "nba": 2027}

FIXTURES_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "kickoff_local",
    "home_team", "away_team", "stadium", "city", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]
REAL_RESULTS_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp"]


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    local_tz = ZoneInfo(cfg.timezone)
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")

    espn_season = ESPN_CURRENT_SEASON[league_id]
    fetch_ts = now_utc_iso()
    games = fetch_real_season_games(league_id, espn_season)

    season_start = datetime.fromisoformat(games[0]["date"].replace("Z", "+00:00")) if games else None

    fixture_rows, result_rows = [], []
    for g in games:
        home = normalize_team_name(g["home_team"], league_id=league_id)
        away = normalize_team_name(g["away_team"], league_id=league_id)
        dt_utc = datetime.fromisoformat(g["date"].replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(local_tz)

        if g["week_number"] is not None:
            matchweek = g["week_number"]
        else:
            matchweek = ((dt_utc - season_start).days // 7) + 1

        match_id = f"{cfg.match_id_prefix}2627_W{matchweek:02d}_{g['event_id']}_{home.replace(' ', '')}_{away.replace(' ', '')}"

        fixture_rows.append({
            "match_id": match_id, "season": SEASON_LABEL, "matchweek": matchweek,
            "date": dt_local.strftime("%Y-%m-%d"), "kickoff_utc": dt_utc.isoformat(), "kickoff_local": dt_local.isoformat(),
            "home_team": home, "away_team": away,
            "stadium": g["venue"], "city": "", "status": "scheduled",
            "source_name": SOURCE_NAME, "source_url_or_page_title": f"https://site.api.espn.com/apis/site/v2/sports/.../{league_id}/scoreboard",
            "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "scheduled_provisional",
            "notes": (
                "Real schedule from ESPN's site API; kickoff time can move with broadcast scheduling -- "
                "re-collect before using kickoff_utc for a leakage-safe cutoff close to game day."
            ),
        })
        if g["completed"] and g["home_score"] is not None and g["away_score"] is not None:
            result_rows.append({
                "match_id": match_id, "home_goals": g["home_score"], "away_goals": g["away_score"],
                "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
            })

    fixtures_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fixtures_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIXTURES_COLUMNS)
        writer.writeheader()
        writer.writerows(fixture_rows)
    print(f"Wrote {len(fixture_rows)} real fixtures to {fixtures_path}")

    with open(real_results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REAL_RESULTS_COLUMNS)
        writer.writeheader()
        writer.writerows(result_rows)
    print(f"Wrote {len(result_rows)} real completed results to {real_results_path}")

    log_data_version(
        dataset_name=f"{league_id}_2026_27_fixtures",
        source_name=SOURCE_NAME, source_timestamp=fetch_ts, row_count=len(fixture_rows),
        is_real_data=True,
        notes=f"{cfg.display_name} {SEASON_LABEL} real schedule from ESPN's site API (season={espn_season}).",
    )


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
