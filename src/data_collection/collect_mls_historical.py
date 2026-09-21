"""Collect real historical MLS results, 2023-2025 seasons.

Source: fixturedownload.com's public JSON feed, one file per real
season (https://fixturedownload.com/feed/json/mls-2023, -2024, -2025)
-- the same source (and fixture-shaped JSON format) every other
bespoke collector in this project uses. Three full, real, completed
seasons (2023: 493 matches/29 teams; 2024: 493 matches/29 teams; 2025:
510 matches/30 teams, San Diego FC's real expansion-team debut season)
-- 1,496 real matches combined, close to a domestic league's own
backtest sample size and far deeper than UEFA Nations League's thin
167-match history.

No football-data.co.uk coverage exists for MLS (it only covers
European domestic leagues) -- this is a bespoke collector, not
`collect_historical_results.py --league mls`.

Does NOT include the current (2026) season -- that is a fixtures list
with real results for already-played matches, collected separately by
collect_mls_fixtures.py, matching how every other league here keeps
"historical" (prior, fully-closed seasons) and "current season
fixtures" in separate files.

Run: python -m src.data_collection.collect_mls_historical
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAGUE_ID = "mls"
SOURCE_NAME = "fixturedownload.com"
SEASONS = ["2023", "2024", "2025"]
RAW_CACHE_DIR = REPO_ROOT / "data" / "external"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "mls_historical_matches.csv"

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team",
    "home_goals", "away_goals", "result",
    "home_xg", "away_xg",
    "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession",
    "home_ppda", "away_ppda",
    "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg",
    "home_red_cards", "away_red_cards",
    "referee", "stadium", "attendance",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

UNAVAILABLE_NOTE = (
    "Advanced metrics (xG, possession, PPDA, big_chances, set_piece_xg), referee, and attendance are "
    "not published by fixturedownload.com and are intentionally left blank rather than estimated."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    rows = []
    for season in SEASONS:
        source_url = f"https://fixturedownload.com/feed/json/mls-{season}"
        resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        cache_path = RAW_CACHE_DIR / f"fixturedownload_mls_{season}.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(resp.content)
        matches = resp.json()

        n_unscored = 0
        for m in matches:
            if m["HomeTeamScore"] is None or m["AwayTeamScore"] is None:
                n_unscored += 1
                continue

            home = normalize_team_name(m["HomeTeam"], league_id=LEAGUE_ID)
            away = normalize_team_name(m["AwayTeam"], league_id=LEAGUE_ID)
            dt_utc = datetime.strptime(m["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
            home_goals, away_goals = int(m["HomeTeamScore"]), int(m["AwayTeamScore"])
            result = "home_win" if home_goals > away_goals else ("away_win" if away_goals > home_goals else "draw")

            match_id = f"MLS{season}_MD{m['RoundNumber']:02d}_{m['MatchNumber']:03d}_{home.replace(' ', '')}_{away.replace(' ', '')}"

            rows.append({
                "season": season, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
                "home_team": home, "away_team": away,
                "home_goals": home_goals, "away_goals": away_goals, "result": result,
                "home_xg": "", "away_xg": "",
                "home_shots": "", "away_shots": "", "home_shots_on_target": "", "away_shots_on_target": "",
                "home_possession": "", "away_possession": "",
                "home_ppda": "", "away_ppda": "",
                "home_big_chances": "", "away_big_chances": "",
                "home_set_piece_xg": "", "away_set_piece_xg": "",
                "home_red_cards": "", "away_red_cards": "",
                "referee": "", "stadium": m.get("Location") or "", "attendance": "",
                "source_name": SOURCE_NAME, "source_url_or_page_title": source_url, "source_timestamp": fetch_ts,
                "is_real_data": True, "data_status": "completed", "notes": UNAVAILABLE_NOTE,
            })
        if n_unscored:
            raise ValueError(
                f"mls-{season} has {n_unscored} unscored match(es) -- expected a fully-completed real season. "
                f"Investigate before treating this as closed historical data."
            )
        print(f"mls-{season}: {len([r for r in rows if r['season'] == season])} real matches")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real historical matches to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="mls_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=True,
        notes=f"MLS {', '.join(SEASONS)} seasons (three full real closed seasons) from fixturedownload.com.",
    )


if __name__ == "__main__":
    main()
