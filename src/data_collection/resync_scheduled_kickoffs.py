"""Re-syncs not-yet-played fixtures' kickoff date/time against the live
fixturedownload.com feed, without touching anything already `completed`.

Real incident this fixes: `collect_fixtures.py` runs once, at league
onboarding -- nothing in this pipeline ever re-fetches the fixture list
afterward (only odds refresh daily). Real broadcaster scheduling moves
kickoffs after that initial collection -- almost always by a day or two
(a placeholder "Saturday 15:00" slot firming up once TV picks a real
time), but real incident confirmed 2026-09-20: La Liga's real matchweek
6 Levante-Athletic Club fixture was postponed a full five weeks, from
2026-09-16 to 2026-10-21. Because `weekly_auto_update.py` waits for
EVERY fixture in a matchweek to conclude before locking any of it, that
one stale date silently stalled the entire matchweek indefinitely --
nine other, already-decided matches sat un-scored and stuck showing
"scheduled" on the live site, including in Trusted Picks.

A stale kickoff_utc has a second, sharper failure mode even for a
same-week drift: if the real kickoff moves LATER than what a daily
automated run's `generated_at` timestamp already is, a prediction
generated in good faith looks "leaked" (generated after its own
recorded kickoff) the moment that matchweek tries to lock --
prediction_ledger.select_pre_kickoff_predictions then refuses to score
it, correctly but for the wrong underlying reason.

Never touches a `completed` row (its date IS what really happened) or
writes a fabricated value -- every date it writes comes from a fresh,
real fetch of the same live source `collect_fixtures.py` itself uses.

Run: python -m src.data_collection.resync_scheduled_kickoffs --league la_liga
     python -m src.data_collection.resync_scheduled_kickoffs  # every league
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import league_path, load_league_config, single_table_league_ids  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402


def resync_league(league_id: str) -> int:
    cfg = load_league_config(league_id)
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    if not fixtures_path.exists():
        print(f"{league_id}: no fixtures file yet, skipping")
        return 0

    source_url = f"https://fixturedownload.com/feed/json/{cfg.fixturedownload_slug}-2026"
    resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    live = resp.json()
    local_tz = ZoneInfo(cfg.timezone)

    live_by_pair: dict[tuple[str, str], str] = {}
    for m in live:
        try:
            home = normalize_team_name(m["HomeTeam"], league_id=league_id)
            away = normalize_team_name(m["AwayTeam"], league_id=league_id)
        except KeyError:
            continue  # a team name this league's registry doesn't know -- not this resync's job to fix
        live_by_pair[(home, away)] = m["DateUtc"]

    with open(fixtures_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    fetch_ts = now_utc_iso()
    n_changed = 0
    for row in rows:
        if row["status"] != "scheduled":
            continue
        live_date = live_by_pair.get((row["home_team"], row["away_team"]))
        if live_date is None:
            continue
        dt_utc = datetime.strptime(live_date, "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=dt_timezone.utc)
        new_kickoff_utc = dt_utc.isoformat()
        if new_kickoff_utc == row["kickoff_utc"]:
            continue
        if dt_utc <= datetime.now(dt_timezone.utc):
            # Real kickoff has already passed by the time we're fetching --
            # writing a "scheduled" row whose own source_timestamp postdates
            # its kickoff is a self-contradictory record (caught for real by
            # tests/test_no_future_leakage.py), and this match is about to
            # be properly locked as `completed` by the next automated run
            # anyway. Leave its (now-stale but not self-contradictory)
            # kickoff_utc alone rather than resync it into a paradox.
            print(f"  {row['match_id']}: real kickoff {new_kickoff_utc} already passed -- leaving as-is, will lock as completed instead")
            continue
        dt_local = dt_utc.astimezone(local_tz)
        print(f"  {row['match_id']}: {row['kickoff_utc']} -> {new_kickoff_utc}")
        row["date"] = dt_local.strftime("%Y-%m-%d")
        row["kickoff_utc"] = new_kickoff_utc
        row["kickoff_local"] = dt_local.isoformat()
        row["source_timestamp"] = fetch_ts
        row["notes"] = (row["notes"] or "") + " [kickoff re-synced against live fixturedownload.com feed]"
        n_changed += 1

    if n_changed:
        with open(fixtures_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"{league_id}: {n_changed} scheduled fixture(s) re-synced")
    return n_changed


def main(league_id: str | None = None) -> None:
    # single_table_league_ids() only -- this assumes the domestic
    # fixtures.csv schema (kickoff_local, no `group` column). UEFA
    # Nations League's own fixture-refresh path is
    # collect_nations_league_fixtures.py, which fully re-collects
    # (real historical data hasn't started locking there yet, so there
    # is no "stuck matchweek" this resync exists to fix).
    for lid in ([league_id] if league_id else single_table_league_ids()):
        resync_league(lid)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default=None, dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
