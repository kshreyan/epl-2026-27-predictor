"""Fetches real, currently-completed 2026-27 match results from
football-data.co.uk's live-updating current-season CSV -- the same
real source (and same file format) `collect_historical_results.py`
uses for 2014/15-2025/26, whose current-season file gets new rows
appended within a day or two of matches being played.

This is the piece that makes `weekly_auto_update.py` real rather than
a design that needs a human to paste in a results CSV every week: it
turns real final scores into exactly the
match_id/home_goals/away_goals/source_name/source_timestamp schema
`update_after_matchweek.run_update()` already expects, by matching
each result to its real match_id in `epl_2026_27_fixtures.csv` via
team-name + date (raising, never guessing, on an unrecognized team
name -- same discipline as every other real collector in this
project).

Before the season's file exists on football-data.co.uk (it is created
once the season has kicked off and the first results come in, not
before), this returns an empty DataFrame -- not an error, since "no
results yet" is an expected, normal state early in the season.
"""
from __future__ import annotations

import csv
import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
CURRENT_SEASON_URL = "https://www.football-data.co.uk/mmz4281/2627/E0.csv"
SOURCE_NAME = "football-data.co.uk"

RESULTS_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp"]


def _parse_date(date_raw: str) -> str:
    try:
        return datetime.strptime(date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.strptime(date_raw, "%d/%m/%y").strftime("%Y-%m-%d")


def fetch_live_results_csv() -> str | None:
    """Returns the raw CSV text, or None if the season's file doesn't
    exist yet on football-data.co.uk (a normal pre-kickoff/early-season
    state, not an error)."""
    resp = requests.get(CURRENT_SEASON_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, allow_redirects=True)
    if resp.status_code != 200 or not resp.text.strip().startswith(("Div", "﻿Div")):
        return None
    return resp.text


def parse_live_results(csv_text: str, fixtures_df: pd.DataFrame) -> pd.DataFrame:
    """Maps every real, completed row in the live CSV to its match_id in
    the real fixtures file via (home_team, away_team) -- unique within a
    season. Raises on an unrecognized team name rather than silently
    dropping the row (the same discipline `normalize_team_name` already
    enforces) and raises if a completed match in the live feed has no
    corresponding fixture (a real data-integrity problem worth seeing
    immediately, not swallowing)."""
    fixture_lookup = {
        (row["home_team"], row["away_team"]): row["match_id"]
        for _, row in fixtures_df.iterrows()
    }

    fetch_ts = now_utc_iso()
    rows = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        home_raw = (row.get("HomeTeam") or "").strip()
        away_raw = (row.get("AwayTeam") or "").strip()
        fthg = (row.get("FTHG") or "").strip()
        ftag = (row.get("FTAG") or "").strip()
        if not home_raw or not away_raw or fthg == "" or ftag == "":
            continue  # not yet played, or a trailing blank row

        home_team = normalize_team_name(home_raw)
        away_team = normalize_team_name(away_raw)
        key = (home_team, away_team)
        if key not in fixture_lookup:
            raise ValueError(
                f"Live result for {home_team} vs {away_team} has no matching fixture in "
                f"{FIXTURES_PATH.name} -- check for a postponement/rearrangement or a fixture-list bug."
            )

        rows.append({
            "match_id": fixture_lookup[key],
            "home_goals": int(fthg),
            "away_goals": int(ftag),
            "source_name": SOURCE_NAME,
            "source_timestamp": fetch_ts,
        })

    return pd.DataFrame(rows, columns=RESULTS_COLUMNS)


def fetch_all_live_results(fixtures_path: Path = FIXTURES_PATH) -> pd.DataFrame:
    """Top-level entry point: real completed 2026-27 results available
    right now, or an empty DataFrame if the season's file doesn't exist
    yet on football-data.co.uk."""
    csv_text = fetch_live_results_csv()
    if csv_text is None:
        return pd.DataFrame(columns=RESULTS_COLUMNS)
    fixtures_df = pd.read_csv(fixtures_path)
    return parse_live_results(csv_text, fixtures_df)


if __name__ == "__main__":
    results = fetch_all_live_results()
    print(f"{len(results)} real completed 2026-27 result(s) available from {SOURCE_NAME}.")
    if not results.empty:
        print(results.to_string(index=False))
