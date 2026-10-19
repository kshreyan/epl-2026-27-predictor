"""Fetches real completed-match results for a UEFA club competition's
current 2026-27 league phase, from the same fixturedownload.com feed
collect_fixtures.py already uses.

Not fetch_live_results.py: that script is football-data.co.uk's
dedicated live-results feed, which only covers domestic leagues
(LeagueConfig.football_data_code required). No such dedicated feed
exists for UEFA club competitions -- fixturedownload.com's own feed is
the only real source, and (same real limitation the old, now-removed
collect_nations_league_historical.py noted for its competition) it has
been observed to lag real-world completion by up to a day. Writing a
separate ledger (rather than trusting collect_fixtures.py's own
`status` column, which this project's domestic collectors deliberately
always set to "scheduled" and leave for the domestic live-results
pipeline to lock) keeps this real limitation explicit and keeps
collect_fixtures.py's shared CSV schema unchanged for every league.

Run: python -m src.data_collection.fetch_continental_cup_live_results --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "fixturedownload.com"

OUTPUT_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp"]


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    output_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    source_url = f"https://fixturedownload.com/feed/json/{cfg.fixturedownload_slug}-2026"

    fetch_ts = now_utc_iso()
    resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    resp.raise_for_status()
    fixtures = resp.json()

    rows = []
    for fx in fixtures:
        if fx["HomeTeamScore"] is None or fx["AwayTeamScore"] is None:
            continue
        home = normalize_team_name(fx["HomeTeam"], league_id=league_id)
        away = normalize_team_name(fx["AwayTeam"], league_id=league_id)
        match_id = f"{cfg.match_id_prefix}2627_MW{fx['RoundNumber']:02d}_{fx['MatchNumber']:03d}_{home.replace(' ', '')}_{away.replace(' ', '')}"
        rows.append({
            "match_id": match_id,
            "home_goals": int(fx["HomeTeamScore"]), "away_goals": int(fx["AwayTeamScore"]),
            "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real completed league-phase results to {output_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
