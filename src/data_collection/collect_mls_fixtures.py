"""Collect the real 2026 MLS fixture list and its already-played results.

Source: fixturedownload.com's public JSON feed
(https://fixturedownload.com/feed/json/mls-2026) -- the same real
source every other league's fixtures come from, confirmed live: 510
matches, 30 real MLS clubs, 35 real match rounds. The real 2026 season
runs Feb-Dec; as of collection this pipeline is onboarding mid-season
(most matches already have a real final score) -- the same real
situation Ligue 1 and La Liga's matchweek 6 were onboarded/caught up
in earlier this project, just for an entire league rather than a few
matchweeks.

Real, observed data gap worth knowing about (not a bug in this
collector): a handful of real 2026 matches with a real, well-past
kickoff date still have no score in this source as of collection (e.g.
New England Revolution v Houston Dynamo FC, 2026-08-08) -- confirmed
directly against the raw feed, not a parsing error here. These are
correctly left `status=scheduled` (never guessed) and the model still
predicts them going forward; they will pick up a real `status=
completed` result whenever this collector is re-run after the source
backfills them.

Not `collect_fixtures.py --league mls`: that shared collector asserts
`n_teams * (n_teams - 1)` fixtures (a full double round-robin), which
holds for every European league here but not MLS -- 510 real matches
for 30 teams (34 games each) is a real, balanced-but-not-round-robin
schedule (see leagues.yaml's comment), not the 870 a full round-robin
would need. This collector's own validation (510 matches, every team
plays a real, equal number of games) reflects the real competition
shape instead.

Writes two files, matching how this project already separates "the
full season's real fixture list" from "results locked so far" for
every other league:
- mls_2026_27_fixtures.csv: all 510 fixtures, `status` set per-row
  from whether a real score already exists.
- mls_2026_27_completed_matches.csv: the real, already-played
  matches, in the same schema historical_matches.csv uses (so
  update_after_matchweek.py-style code can concatenate it directly for
  refitting) -- this is what "locks" mid-season onboarding for a
  single league in one collection pass, rather than needing a
  matchweek-by-matchweek skip_scoring catch-up loop the way Ligue 1
  and La Liga were onboarded.

Run: python -m src.data_collection.collect_mls_fixtures
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
LEAGUE_ID = "mls"
SOURCE_NAME = "fixturedownload.com"
SEASON = "2026-27"  # filename-compatibility label only -- the real season is "2026" (see leagues.yaml)
EXPECTED_TOTAL_MATCHES = 510
EXPECTED_MATCHES_PER_TEAM = 34

FIXTURES_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "kickoff_local",
    "home_team", "away_team", "stadium", "city", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]
COMPLETED_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "home_goals", "away_goals", "result",
    "home_xg", "away_xg", "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession", "home_ppda", "away_ppda", "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg", "home_red_cards", "away_red_cards", "referee", "stadium",
    "attendance", "source_name", "source_url_or_page_title", "source_timestamp", "is_real_data", "data_status", "notes",
]


def main() -> None:
    cfg = load_league_config(LEAGUE_ID)
    raw_cache_path = REPO_ROOT / "data" / "external" / "fixturedownload_mls_2026.json"
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(LEAGUE_ID, "2026_27_fixtures.csv")
    completed_path = REPO_ROOT / "data" / "raw" / league_path(LEAGUE_ID, "2026_27_completed_matches.csv")
    source_url = f"https://fixturedownload.com/feed/json/{cfg.fixturedownload_slug}-2026"

    fetch_ts = now_utc_iso()
    resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    raw_cache_path.parent.mkdir(parents=True, exist_ok=True)
    raw_cache_path.write_bytes(resp.content)
    fixtures = resp.json()

    if len(fixtures) != EXPECTED_TOTAL_MATCHES:
        raise ValueError(f"Expected {EXPECTED_TOTAL_MATCHES} 2026 MLS matches, got {len(fixtures)}.")

    fixture_rows, completed_rows = [], []
    n_completed = 0
    for fx in fixtures:
        home = normalize_team_name(fx["HomeTeam"], league_id=LEAGUE_ID)
        away = normalize_team_name(fx["AwayTeam"], league_id=LEAGUE_ID)
        dt_utc = datetime.strptime(fx["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        match_id = (
            f"{cfg.match_id_prefix}2627_MD{fx['RoundNumber']:02d}_{fx['MatchNumber']:03d}_"
            f"{home.replace(' ', '')}_{away.replace(' ', '')}"
        )
        has_score = fx["HomeTeamScore"] is not None and fx["AwayTeamScore"] is not None
        status = "completed" if has_score else "scheduled"

        fixture_rows.append({
            "match_id": match_id, "season": SEASON, "matchweek": fx["RoundNumber"],
            "date": dt_utc.strftime("%Y-%m-%d"), "kickoff_utc": dt_utc.isoformat(),
            "kickoff_local": dt_utc.isoformat(),  # real per-city local time not resolvable from this feed alone
            "home_team": home, "away_team": away, "stadium": fx.get("Location") or "", "city": "",
            "status": status, "source_name": SOURCE_NAME, "source_url_or_page_title": source_url,
            "source_timestamp": fetch_ts, "is_real_data": True,
            "data_status": "completed" if has_score else "scheduled_provisional",
            "notes": (
                "Real final score, locked at onboarding." if has_score else
                "Kickoff time reflects originally-published scheduling; MLS broadcaster picks can move this "
                "fixture. Re-collect before using kickoff_utc for a leakage-safe cutoff close to matchday."
            ),
        })

        if has_score:
            n_completed += 1
            home_goals, away_goals = int(fx["HomeTeamScore"]), int(fx["AwayTeamScore"])
            result = "home_win" if home_goals > away_goals else ("away_win" if away_goals > home_goals else "draw")
            completed_rows.append({
                "season": SEASON, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
                "home_team": home, "away_team": away,
                "home_goals": home_goals, "away_goals": away_goals, "result": result,
                "home_xg": "", "away_xg": "", "home_shots": "", "away_shots": "",
                "home_shots_on_target": "", "away_shots_on_target": "", "home_possession": "", "away_possession": "",
                "home_ppda": "", "away_ppda": "", "home_big_chances": "", "away_big_chances": "",
                "home_set_piece_xg": "", "away_set_piece_xg": "", "home_red_cards": "", "away_red_cards": "",
                "referee": "", "stadium": fx.get("Location") or "", "attendance": "",
                "source_name": SOURCE_NAME, "source_url_or_page_title": source_url, "source_timestamp": fetch_ts,
                "is_real_data": True, "data_status": "completed",
                "notes": "Real final score from fixturedownload.com, locked at league onboarding (mid-season).",
            })

    matches_per_team: dict[str, int] = {}
    for r in fixture_rows:
        matches_per_team[r["home_team"]] = matches_per_team.get(r["home_team"], 0) + 1
        matches_per_team[r["away_team"]] = matches_per_team.get(r["away_team"], 0) + 1
    bad = {t: n for t, n in matches_per_team.items() if n != EXPECTED_MATCHES_PER_TEAM}
    if bad:
        raise ValueError(f"Expected every team to play {EXPECTED_MATCHES_PER_TEAM} real matches, got: {bad}")

    fixtures_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fixtures_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIXTURES_COLUMNS)
        writer.writeheader()
        writer.writerows(fixture_rows)
    print(f"Wrote {len(fixture_rows)} fixtures to {fixtures_path} ({n_completed} already completed)")

    with open(completed_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COMPLETED_COLUMNS)
        writer.writeheader()
        writer.writerows(completed_rows)
    print(f"Wrote {len(completed_rows)} real completed matches to {completed_path}")

    log_data_version(
        dataset_name="mls_2026_27_fixtures", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(fixture_rows), is_real_data=True,
        notes=f"MLS 2026 fixture list from fixturedownload.com ({n_completed} real results locked at onboarding).",
    )


if __name__ == "__main__":
    main()
