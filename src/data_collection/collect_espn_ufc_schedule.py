"""Collect the real upcoming/recent UFC fight-card schedule from
ESPN's site API (see espn_mma_api.py for the real data shape this
reads). One row per real FIGHT (not per event -- a fight card has many
real fights), the same "one row per match" convention every other
league's fixtures CSV uses, with event metadata repeated across every
fight on that real card.

Unlike NFL/NBA/NHL/NCAA Football, fighter names are NOT run through a
canonical alias table -- a roster of hundreds of active real fighters
makes a hand-maintained list impractical (see team_names.py's module
docstring and config/leagues.yaml's UFC note). ESPN's own real
`fullName` is used directly; a real spelling mismatch against The Odds
API surfaces as that one fight getting no real market odds, never a
guessed mapping.

Writes three real outputs from the SAME fetch, same convention as
collect_espn_schedule.py:
1. `ufc_2026_27_fight_card.csv` -- every real fight in the window,
   `status` "scheduled" or "completed" (UFC events are sparse and
   date-driven, not weekly-locked, so this collector itself marks a
   fight completed once ESPN reports a real result -- unlike the
   weekly team-sport leagues' separate results ledger).
2. `ufc_2026_27_real_results.csv` -- real completed fights only
   (match_id, winner, method, finish_round).
3. `ufc_2026_27_fixtures.csv` -- a thin real adapter over the same
   fight-card rows (home_team=fighter_a, away_team=fighter_b,
   matchweek=a real sequential event index, NOT a calendar week -- UFC
   has no real weekly cadence) so the shared, format-agnostic
   collect_odds.py (which expects a generic home_team/away_team
   fixtures file) needs zero UFC-specific code, same as every other
   league.

Run: python -m src.data_collection.collect_espn_ufc_schedule
"""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_collection.espn_mma_api import fetch_real_ufc_events  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "site.api.espn.com"
SEASON_LABEL = "2026-27"

# A real rolling window: 60 real days back (recently completed cards,
# for live results) through 180 real days forward (announced upcoming
# cards -- UFC books fights months out) -- wide enough to catch every
# real currently-relevant card without an unbounded historical fetch
# (that is collect_espn_ufc_historical.py's job).
DAYS_BACK = 60
DAYS_FORWARD = 180

FIGHT_CARD_COLUMNS = [
    "match_id", "season", "event_id", "event_name", "date", "kickoff_utc",
    "fighter_a", "fighter_b", "weight_class", "scheduled_rounds",
    "venue_city", "venue_country", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]
REAL_RESULTS_COLUMNS = ["match_id", "winner", "method", "finish_round", "source_name", "source_timestamp"]
# Generic adapter schema collect_odds.py actually reads -- see module docstring.
FIXTURES_ADAPTER_COLUMNS = ["match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team"]


def main() -> None:
    cfg = load_league_config("ufc")
    fight_card_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_fight_card.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_real_results.csv")

    fetch_ts = now_utc_iso()
    date_from = date.today() - timedelta(days=DAYS_BACK)
    date_to = date.today() + timedelta(days=DAYS_FORWARD)
    events = fetch_real_ufc_events(date_from, date_to)

    fight_rows, result_rows = [], []
    for ev in events:
        for f in ev["fights"]:
            dt_utc = datetime.fromisoformat(f["date"].replace("Z", "+00:00"))
            match_id = f"{cfg.match_id_prefix}2627_{ev['event_id']}_{f['fight_id']}"
            status = "completed" if f["completed"] else "scheduled"
            fight_rows.append({
                "match_id": match_id, "season": SEASON_LABEL,
                "event_id": ev["event_id"], "event_name": ev["event_name"],
                "date": dt_utc.strftime("%Y-%m-%d"), "kickoff_utc": dt_utc.isoformat(),
                "fighter_a": f["fighter_a_name"], "fighter_b": f["fighter_b_name"],
                "weight_class": f["weight_class"], "scheduled_rounds": f["scheduled_rounds"],
                "venue_city": ev["venue_city"], "venue_country": ev["venue_country"], "status": status,
                "source_name": SOURCE_NAME, "source_url_or_page_title": "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard",
                "source_timestamp": fetch_ts, "is_real_data": True,
                "data_status": "completed" if f["completed"] else "scheduled_provisional",
                "notes": "Real fight-card data from ESPN's site API; a scheduled fight can still be moved/cancelled before fight night.",
            })
            if f["completed"] and f["method"] != "unscored":
                winner = "fighter_a" if f["winner_id"] == f["fighter_a_id"] else ("fighter_b" if f["winner_id"] == f["fighter_b_id"] else "")
                result_rows.append({
                    "match_id": match_id, "winner": winner, "method": f["method"],
                    "finish_round": f["finish_round"] or "", "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
                })

    fight_card_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fight_card_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIGHT_CARD_COLUMNS)
        writer.writeheader()
        writer.writerows(fight_rows)
    print(f"Wrote {len(fight_rows)} real fights ({len(events)} real events) to {fight_card_path}")

    with open(real_results_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REAL_RESULTS_COLUMNS)
        writer.writeheader()
        writer.writerows(result_rows)
    print(f"Wrote {len(result_rows)} real completed results to {real_results_path}")

    # Real sequential event index (by real event date), used only as
    # collect_odds.py's generic "matchweek" field -- see module docstring.
    event_order = {eid: i + 1 for i, eid in enumerate(dict.fromkeys(r["event_id"] for r in sorted(fight_rows, key=lambda r: r["date"])))}
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_fixtures.csv")
    with open(fixtures_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIXTURES_ADAPTER_COLUMNS)
        writer.writeheader()
        writer.writerows([
            {
                "match_id": r["match_id"], "season": r["season"], "matchweek": event_order[r["event_id"]],
                "date": r["date"], "kickoff_utc": r["kickoff_utc"],
                "home_team": r["fighter_a"], "away_team": r["fighter_b"],
            }
            for r in fight_rows
        ])
    print(f"Wrote {len(fight_rows)} rows to the generic fixtures adapter {fixtures_path} (for collect_odds.py)")

    log_data_version(
        dataset_name="ufc_2026_27_fight_card", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(fight_rows), is_real_data=True,
        notes=f"UFC real fight-card window [{date_from}, {date_to}] from ESPN's site API.",
    )


if __name__ == "__main__":
    main()
