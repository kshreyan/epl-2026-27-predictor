"""Collect real NHL fixtures/historical results from the NHL's own
official public API (api-web.nhle.com), confirmed directly this
session (HTTP 200, real schema) as richer than ESPN's site API for
this one sport: the same real per-team schedule endpoint carries each
real game's `periodDescriptor.periodType` (REG/OT/SO -- the real
information needed for NHL's own real points standings, where an
OT/shootout loss earns 1 real point and a regulation loss earns 0,
something plain win/loss can't represent), which ESPN's schedule
endpoint does not expose at all. Replaces collect_espn_schedule.py/
collect_espn_historical.py for NHL only; NBA/NCAA Football are
unaffected and keep using ESPN.

One real call per (team, season) -- the same per-team iteration
pattern collect_espn_schedule.py already uses for every "points"-
format league (no real league-wide season schedule endpoint was found
on api-web.nhle.com); real games are deduplicated by their real game
id since each one appears in both participating teams' own schedules.

Output schema matches collect_espn_schedule.py/collect_espn_historical
.py's real column contract (match_id/season/matchweek/...) so every
existing downstream consumer needs zero changes; `period_type` is a
new real extra column (REG/OT/SO) consumed by
simulate_team_sport_season.py's real points-standings fix.

Run: python -m src.data_collection.collect_nhl_apiweb
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "api-web.nhle.com (NHL's official public API)"
SEASON_LABEL = "2026-27"
CURRENT_SEASON_ID = "20262027"
N_PRIOR_SEASONS = 5
REQUEST_TIMEOUT = 20

# Real, current 32-team roster (confirmed live this session via
# /v1/standings/now) plus "ARI" -- the Arizona Coyotes' real code before
# their real 2024 relocation to Utah, which real games from the
# 2021-22 through 2023-24 seasons (inside this collector's real
# 5-prior-season window) still use. normalize_team_name() already
# resolves "Arizona Coyotes" -> "Utah Mammoth" via its real existing
# alias table -- not duplicated here.
TEAM_CODES = [
    "ANA", "ARI", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI",
    "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH",
]
RAW_NAME_BY_CODE = {
    "ANA": "Anaheim Ducks", "ARI": "Arizona Coyotes", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres",
    "CAR": "Carolina Hurricanes", "CBJ": "Columbus Blue Jackets", "CGY": "Calgary Flames",
    "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche", "DAL": "Dallas Stars", "DET": "Detroit Red Wings",
    "EDM": "Edmonton Oilers", "FLA": "Florida Panthers", "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens", "NJD": "New Jersey Devils", "NSH": "Nashville Predators",
    "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "SEA": "Seattle Kraken",
    "SJS": "San Jose Sharks", "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs", "UTA": "Utah Mammoth", "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights", "WPG": "Winnipeg Jets", "WSH": "Washington Capitals",
}

FIXTURES_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "kickoff_local",
    "home_team", "away_team", "stadium", "city", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes", "period_type",
]
REAL_RESULTS_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp", "period_type"]
HISTORICAL_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "week_number",
    "home_score", "away_score", "result",
    "venue", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes", "period_type",
]
COMPLETED_STATES = {"FINAL", "OFF"}


def _season_id(end_year: int) -> str:
    return f"{end_year - 1}{end_year}"


def _fetch_team_season(team_code: str, season_id: str) -> list[dict]:
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_code}/{season_id}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        return []
    return resp.json().get("games", [])


def main() -> None:
    cfg = load_league_config("nhl")
    from zoneinfo import ZoneInfo
    local_tz = ZoneInfo(cfg.timezone)

    fixtures_path = REPO_ROOT / "data" / "raw" / "nhl_2026_27_fixtures.csv"
    real_results_path = REPO_ROOT / "data" / "raw" / "nhl_2026_27_real_results.csv"
    historical_path = REPO_ROOT / "data" / "raw" / "nhl_historical_matches.csv"

    fetch_ts = now_utc_iso()
    current_end_year = 2027
    season_ids = [CURRENT_SEASON_ID] + [_season_id(y) for y in range(current_end_year - N_PRIOR_SEASONS, current_end_year)]

    games_by_id: dict[int, dict] = {}
    for team_code in TEAM_CODES:
        for season_id in season_ids:
            for g in _fetch_team_season(team_code, season_id):
                if g.get("gameType") != 2:  # real regular season only (1=preseason, 3=playoffs)
                    continue
                games_by_id[g["id"]] = g

    season_start_by_id: dict[str, datetime] = {}
    for season_id in season_ids:
        season_games = [g for g in games_by_id.values() if str(g["season"]) == season_id]
        if season_games:
            season_start_by_id[season_id] = min(
                datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00")) for g in season_games
            )

    fixture_rows, result_rows, historical_rows = [], [], []
    for g in sorted(games_by_id.values(), key=lambda g: g["startTimeUTC"]):
        season_id = str(g["season"])
        home_code, away_code = g["homeTeam"]["abbrev"], g["awayTeam"]["abbrev"]
        home = normalize_team_name(RAW_NAME_BY_CODE[home_code], league_id="nhl")
        away = normalize_team_name(RAW_NAME_BY_CODE[away_code], league_id="nhl")
        dt_utc = datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00"))
        season_start = season_start_by_id[season_id]
        week = ((dt_utc - season_start).days // 7) + 1
        period_type = g.get("periodDescriptor", {}).get("periodType", "")
        match_id = f"NHL2627_W{week:02d}_{g['id']}"

        completed = g.get("gameState") in COMPLETED_STATES
        home_score, away_score = g["homeTeam"].get("score"), g["awayTeam"].get("score")

        if season_id == CURRENT_SEASON_ID:
            dt_local = dt_utc.astimezone(local_tz)
            fixture_rows.append({
                "match_id": match_id, "season": SEASON_LABEL, "matchweek": week,
                "date": dt_local.strftime("%Y-%m-%d"), "kickoff_utc": dt_utc.isoformat(), "kickoff_local": dt_local.isoformat(),
                "home_team": home, "away_team": away,
                "stadium": g.get("venue", {}).get("default", ""), "city": "", "status": "scheduled",
                "source_name": SOURCE_NAME, "source_url_or_page_title": "https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}",
                "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "scheduled_provisional",
                "notes": "Real schedule from the NHL's own official public API.",
                "period_type": period_type if completed else "",
            })
            if completed and home_score is not None and away_score is not None:
                result_rows.append({
                    "match_id": match_id, "home_goals": home_score, "away_goals": away_score,
                    "source_name": SOURCE_NAME, "source_timestamp": fetch_ts, "period_type": period_type,
                })
        else:
            if not (completed and home_score is not None and away_score is not None):
                continue
            result = "home_win" if home_score > away_score else ("away_win" if away_score > home_score else "draw")
            historical_rows.append({
                "season": f"{int(season_id[:4])}", "match_id": match_id, "date": g["gameDate"],
                "home_team": home, "away_team": away, "week_number": week,
                "home_score": home_score, "away_score": away_score, "result": result,
                "venue": g.get("venue", {}).get("default", ""), "source_name": SOURCE_NAME,
                "source_url_or_page_title": "https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}",
                "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "completed",
                "notes": "", "period_type": period_type,
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

    with open(historical_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(historical_rows)
    print(f"Wrote {len(historical_rows)} real historical games to {historical_path}")

    log_data_version(
        dataset_name="nhl_2026_27_fixtures", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(fixture_rows), is_real_data=True,
        notes=f"NHL {SEASON_LABEL} real schedule + historical from the NHL's own official public API.",
    )


if __name__ == "__main__":
    main()
