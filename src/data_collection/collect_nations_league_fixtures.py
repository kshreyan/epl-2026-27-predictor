"""Collect the real 2026-27 UEFA Nations League fixture list.

Source: fixturedownload.com's public JSON feed
(https://fixturedownload.com/feed/json/nations-league-2026) -- the
same real source every other league's fixtures come from, confirmed
live: 156 matches across League A/B/C/D, 54 real UEFA member
associations, six match rounds (Round 1-4: 2026-09-24 to 2026-10-06,
the current international break; Round 5-6: 2026-11-12 to 2026-11-17,
the next one).

This is a bespoke collector, not `collect_fixtures.py --league
nations_league`: that shared collector asserts
`n_teams * (n_teams - 1)` fixtures (a full single round-robin double
season), which is real and correct for every `format: single_table`
league but does not hold here -- Nations League splits into groups of
3-4 teams that only play each other, not a full round-robin across all
54 teams. This collector's own validation (156 matches, every team
plays a real number of group matches) reflects the real competition
shape instead of forcing a domestic-league assumption onto it.

Run: python -m src.data_collection.collect_nations_league_fixtures
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAGUE_ID = "nations_league"
SOURCE_NAME = "fixturedownload.com"
SEASON = "2026-27"
EXPECTED_TOTAL_MATCHES = 156
EXPECTED_ROUNDS = 6

OUTPUT_COLUMNS = [
    "match_id", "season", "matchweek", "group", "date", "kickoff_utc",
    "home_team", "away_team", "stadium", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]


def main() -> None:
    cfg = load_league_config(LEAGUE_ID)
    raw_cache_path = REPO_ROOT / "data" / "external" / f"fixturedownload_{LEAGUE_ID}_2026_27.json"
    output_path = REPO_ROOT / "data" / "raw" / league_path(LEAGUE_ID, "2026_27_fixtures.csv")
    source_url = f"https://fixturedownload.com/feed/json/{cfg.fixturedownload_slug}-2026"

    fetch_ts = now_utc_iso()
    resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    raw_cache_path.parent.mkdir(parents=True, exist_ok=True)
    raw_cache_path.write_bytes(resp.content)
    fixtures = resp.json()

    if len(fixtures) != EXPECTED_TOTAL_MATCHES:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_MATCHES} 2026-27 Nations League matches, got {len(fixtures)}. "
            f"Refusing to write a fixture file that doesn't match the real published schedule."
        )
    rounds = {fx["RoundNumber"] for fx in fixtures}
    if rounds != set(range(1, EXPECTED_ROUNDS + 1)):
        raise ValueError(f"Expected rounds 1-{EXPECTED_ROUNDS}, got {sorted(rounds)}.")

    rows = []
    for fx in fixtures:
        home = normalize_team_name(fx["HomeTeam"], league_id=LEAGUE_ID)
        away = normalize_team_name(fx["AwayTeam"], league_id=LEAGUE_ID)
        dt_utc = datetime.strptime(fx["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)

        match_id = (
            f"{cfg.match_id_prefix}2627_MD{fx['RoundNumber']:02d}_{fx['MatchNumber']:03d}_"
            f"{home.replace(' ', '')}_{away.replace(' ', '')}"
        )

        rows.append({
            "match_id": match_id,
            "season": SEASON,
            "matchweek": fx["RoundNumber"],
            "group": fx.get("Group") or "",
            "date": dt_utc.strftime("%Y-%m-%d"),
            "kickoff_utc": dt_utc.isoformat(),
            "home_team": home,
            "away_team": away,
            "stadium": fx.get("Location") or "",
            "status": "scheduled",
            "source_name": SOURCE_NAME,
            "source_url_or_page_title": source_url,
            "source_timestamp": fetch_ts,
            "is_real_data": True,
            "data_status": "scheduled_provisional",
            "notes": (
                "Kickoff time reflects originally-published scheduling. Groups of 3-4 teams -- not a "
                "full round-robin across all 54 teams (see module docstring)."
            ),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} fixtures to {output_path}")

    log_data_version(
        dataset_name=f"{LEAGUE_ID}_2026_27_fixtures",
        source_name=SOURCE_NAME,
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=True,
        notes=f"{cfg.display_name} 2026-27 fixture list from fixturedownload.com (Round 1-6, groups A-D).",
    )


if __name__ == "__main__":
    main()
