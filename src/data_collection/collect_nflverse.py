"""Collect real NFL fixtures/historical results from nflverse's public
`nfldata` repository (raw.githubusercontent.com/nflverse/nfldata/
master/data/games.csv) -- confirmed directly (HTTP 200, real schema)
this session as a working, free, no-key-required source that is
genuinely richer than ESPN's site API for this one sport: the same
real file already carries rest days, real closing spread/moneyline/
total lines and odds, weather (temp/wind/roof/surface), and starting
QB names -- fields ESPN's schedule endpoint does not expose at all.
Replaces collect_espn_schedule.py/collect_espn_historical.py for NFL
only; NBA/NCAA Football are unaffected and keep using ESPN.

Output schema matches collect_espn_schedule.py/collect_espn_historical
.py's real column contract exactly (match_id/season/matchweek/...) so
every existing downstream consumer (point_margin_model.py,
backtest_team_sport.py, the dashboard JSON builders, the frontend)
needs zero changes -- the extra real columns this source adds
(home_qb_name, away_qb_name, home_rest, away_rest, real closing
spread_line/total_line/moneylines, temp, wind, roof, surface,
div_game) are appended alongside, for the NFL-specific QB-rating and
GBM models introduced in this phase to consume; every other reader
simply ignores them (pandas tolerates extra columns).

`gametime` is nflverse's own real local kickoff time -- confirmed
directly this session by cross-checking a real Week 1 game's
`gameday`+`gametime` ("2026-09-09", "20:20") against this project's
existing ESPN-sourced kickoff_utc for the identical real game
(2026-09-10T00:20:00+00:00): 20:20 only reconciles to that real UTC
instant as US/Eastern, not the home team's own local zone (Seattle's
real Week 1 home game would be an implausible near-midnight Pacific
kickoff otherwise) -- the real nflverse convention is Eastern, not
stadium-local, confirmed empirically rather than assumed from
undocumented behavior.

Real, honest limitation: nflverse's `games.csv` does not carry
play-by-play data, so no real EPA (expected points added) feature is
available from this source alone -- that needs a separate, much
larger real play-by-play ingestion (nflverse also publishes this, as
`play_by_play_<season>.csv.gz` release assets) that is out of this
phase's scope; EPA is deferred and should not be assumed present
anywhere downstream of this collector.

Run: python -m src.data_collection.collect_nflverse
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import load_league_config  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "nflverse (raw.githubusercontent.com/nflverse/nfldata)"
SOURCE_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
SEASON_LABEL = "2026-27"
CURRENT_SEASON = 2026
N_PRIOR_SEASONS = 5
NFLVERSE_LOCAL_TZ = ZoneInfo("America/New_York")

# Real, stable public fact (NFL team codes/franchises), confirmed
# against nflverse's own 2026-season rows this session -- not guessed.
# Every code appearing in the 2021-2026 window already uses its
# current (post-relocation) code, so no historical-code remapping is
# needed for this collector's window.
NFLVERSE_TEAM_CODE_TO_CANONICAL = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

FIXTURES_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "kickoff_local",
    "home_team", "away_team", "stadium", "city", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
    # Real nflverse-only extras, for the QB-rating/GBM models.
    "home_qb_name", "away_qb_name", "home_rest", "away_rest",
    "spread_line", "home_moneyline", "away_moneyline", "total_line",
    "temp", "wind", "roof", "surface", "div_game",
]
REAL_RESULTS_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp"]
HISTORICAL_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "week_number",
    "home_score", "away_score", "result",
    "venue", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
    "home_qb_name", "away_qb_name", "home_rest", "away_rest",
    "spread_line", "home_moneyline", "away_moneyline", "total_line",
    "temp", "wind", "roof", "surface", "div_game",
]
EPA_NOTE = (
    "nflverse games.csv has no play-by-play, so no real EPA feature is available from this file alone -- "
    "deferred, not estimated (see module docstring)."
)


def _fetch_games_csv() -> list[dict]:
    resp = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    return list(csv.DictReader(resp.text.splitlines()))


def _kickoff_utc(gameday: str, gametime: str) -> datetime | None:
    if not gameday or not gametime:
        return None
    local = datetime.strptime(f"{gameday} {gametime}", "%Y-%m-%d %H:%M").replace(tzinfo=NFLVERSE_LOCAL_TZ)
    return local.astimezone(ZoneInfo("UTC"))


def _float_or_blank(raw: str):
    return float(raw) if raw not in (None, "") else ""


def main() -> None:
    cfg = load_league_config("nfl")
    local_tz = ZoneInfo(cfg.timezone)
    fixtures_path = REPO_ROOT / "data" / "raw" / "nfl_2026_27_fixtures.csv"
    real_results_path = REPO_ROOT / "data" / "raw" / "nfl_2026_27_real_results.csv"
    historical_path = REPO_ROOT / "data" / "raw" / "nfl_historical_matches.csv"

    fetch_ts = now_utc_iso()
    all_games = _fetch_games_csv()
    reg_games = [g for g in all_games if g["game_type"] == "REG"]

    fixture_rows, result_rows, historical_rows = [], [], []
    n_fixture_season = 0

    for g in reg_games:
        season = int(g["season"])
        if season < CURRENT_SEASON - N_PRIOR_SEASONS or season > CURRENT_SEASON:
            continue
        home = NFLVERSE_TEAM_CODE_TO_CANONICAL[g["home_team"]]
        away = NFLVERSE_TEAM_CODE_TO_CANONICAL[g["away_team"]]
        week = int(g["week"])
        dt_utc = _kickoff_utc(g["gameday"], g["gametime"])
        match_id = f"NFL2627_W{week:02d}_{g['game_id']}"
        extras = {
            "home_qb_name": g.get("home_qb_name", ""), "away_qb_name": g.get("away_qb_name", ""),
            "home_rest": g.get("home_rest", ""), "away_rest": g.get("away_rest", ""),
            "spread_line": g.get("spread_line", ""), "home_moneyline": g.get("home_moneyline", ""),
            "away_moneyline": g.get("away_moneyline", ""), "total_line": g.get("total_line", ""),
            "temp": g.get("temp", ""), "wind": g.get("wind", ""),
            "roof": g.get("roof", ""), "surface": g.get("surface", ""), "div_game": g.get("div_game", ""),
        }
        home_score = g.get("home_score") or ""
        away_score = g.get("away_score") or ""
        completed = home_score != "" and away_score != ""

        if season == CURRENT_SEASON:
            n_fixture_season += 1
            dt_local = dt_utc.astimezone(local_tz) if dt_utc else None
            fixture_rows.append({
                "match_id": match_id, "season": SEASON_LABEL, "matchweek": week,
                "date": dt_local.strftime("%Y-%m-%d") if dt_local else g["gameday"],
                "kickoff_utc": dt_utc.isoformat() if dt_utc else "",
                "kickoff_local": dt_local.isoformat() if dt_local else "",
                "home_team": home, "away_team": away,
                "stadium": g.get("stadium", ""), "city": "", "status": "scheduled",
                "source_name": SOURCE_NAME, "source_url_or_page_title": SOURCE_URL,
                "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "scheduled_provisional",
                "notes": (
                    "Real schedule from nflverse's nfldata repository; rest/weather/QB/real closing-line "
                    f"columns are this real source's own fields. {EPA_NOTE}"
                ),
                **extras,
            })
            if completed:
                result_rows.append({
                    "match_id": match_id, "home_goals": int(home_score), "away_goals": int(away_score),
                    "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
                })
        else:
            if not completed:
                continue  # a real past season should be fully played out; skip rather than fabricate
            result = "home_win" if int(home_score) > int(away_score) else ("away_win" if int(away_score) > int(home_score) else "draw")
            historical_rows.append({
                "season": str(season), "match_id": match_id, "date": g["gameday"],
                "home_team": home, "away_team": away, "week_number": week,
                "home_score": int(home_score), "away_score": int(away_score), "result": result,
                "venue": g.get("stadium", ""), "source_name": SOURCE_NAME,
                "source_url_or_page_title": SOURCE_URL, "source_timestamp": fetch_ts,
                "is_real_data": True, "data_status": "completed", "notes": EPA_NOTE,
                **extras,
            })

    historical_rows.sort(key=lambda r: r["date"])

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
    seasons_covered = sorted({r["season"] for r in historical_rows})
    print(f"Wrote {len(historical_rows)} real historical games to {historical_path} "
          f"({seasons_covered[0]}-{seasons_covered[-1]})" if seasons_covered else f"Wrote 0 real historical games to {historical_path}")

    log_data_version(
        dataset_name="nfl_2026_27_fixtures", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(fixture_rows), is_real_data=True,
        notes=f"NFL {SEASON_LABEL} real schedule + historical from nflverse's nfldata repository.",
    )


if __name__ == "__main__":
    main()
