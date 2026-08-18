"""Match-odds (1X2 + totals + BTTS) collector for the 2026-27 season.

Uses The Odds API (https://the-odds-api.com/) when a real API key is
configured -- read from the `ODDS_API_KEY` environment variable (via a
local, gitignored `.env` file; see `.env.example`), never hardcoded,
never committed. Their terms permit using this data inside a broader
analytical dashboard (not reselling it as a standalone data product),
which is what this project does.

**Without a configured key, this script does exactly what it did
before**: writes one `data_status=unavailable` sentinel row per real
fixture (spec section 5.6 / 17 "If market odds are unavailable, use
model-only mode"). `market_available` must be derived as False from
those rows.

**With a configured key**: fetches the current EPL h2h (1X2) market,
writes one real row per (fixture, bookmaker) actually returned by the
API, and leaves every fixture the API doesn't cover yet (bookmakers
only post markets shortly before kickoff -- most of the 380 fixtures,
this early) as the same honest sentinel row as before. Raw per-
bookmaker decimal odds are written as returned; overround removal and
cross-bookmaker log-odds averaging happen downstream in
`src/features/build_market_features.py`, not here.

Only `current_*_odds` are ever populated by this collector -- The Odds
API's free tier does not provide historical opening/closing snapshots,
so `opening_*_odds` and `closing_*_odds` stay blank + flagged, not
estimated.

Run: python -m src.data_collection.collect_odds
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed -- ODDS_API_KEY can still come from a real env var

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv"

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "").strip()
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
SOURCE_NAME = "the-odds-api.com"

OUTPUT_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team",
    "bookmaker", "market_type",
    "opening_home_odds", "opening_draw_odds", "opening_away_odds",
    "current_home_odds", "current_draw_odds", "current_away_odds",
    "closing_home_odds", "closing_draw_odds", "closing_away_odds",
    "over_2_5_odds", "under_2_5_odds", "btts_yes_odds", "btts_no_odds",
    "odds_snapshot_type", "time_to_kickoff_hours", "odds_format", "odds_timestamp",
    "source_name", "source_url_or_page_title", "is_example", "is_real_data",
    "data_status", "collection_date", "notes",
]

SENTINEL_NOTE = (
    "No live odds-API subscription is connected to this pipeline (ODDS_API_KEY not set). Row exists "
    "only to preserve a match_id join for downstream code; market_available must be derived as False. "
    "Model predictions run in model-only mode until a real key is provided -- see .env.example."
)
UNCOVERED_NOTE = (
    "The Odds API is configured and reachable, but has not yet posted a market for this fixture "
    "(bookmakers typically open markets ~1-2 weeks before kickoff) -- genuinely unavailable, not a "
    "collector failure."
)


def sentinel_row(fx: dict, fetch_ts: str, note: str) -> dict:
    return {
        "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
        "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": fx["home_team"], "away_team": fx["away_team"],
        "bookmaker": "", "market_type": "1X2",
        "opening_home_odds": "", "opening_draw_odds": "", "opening_away_odds": "",
        "current_home_odds": "", "current_draw_odds": "", "current_away_odds": "",
        "closing_home_odds": "", "closing_draw_odds": "", "closing_away_odds": "",
        "over_2_5_odds": "", "under_2_5_odds": "", "btts_yes_odds": "", "btts_no_odds": "",
        "odds_snapshot_type": "unknown", "time_to_kickoff_hours": "", "odds_format": "decimal",
        # source_name is ALWAYS "none_available" here, regardless of whether
        # ODDS_API_KEY is configured: is_real_data=False on every sentinel
        # row, and a populated source_name next to is_real_data=False would
        # misleadingly suggest a real fetch happened for this specific row.
        # (An earlier version set this to the real source name whenever a
        # key was merely *configured*, even on a failed/empty fetch --
        # caught during review and fixed here.)
        "odds_timestamp": fetch_ts, "source_name": "none_available",
        "source_url_or_page_title": "", "is_example": False, "is_real_data": False,
        "data_status": "unavailable", "collection_date": fetch_ts[:10], "notes": note,
    }


def fetch_real_odds(fetch_ts: str) -> tuple[dict[str, list[dict]], str | None]:
    """Returns (match_id -> list of real per-bookmaker row dicts, error_message_or_None)."""
    resp = requests.get(ODDS_API_URL, params={
        "apiKey": ODDS_API_KEY, "regions": "uk", "markets": "h2h", "oddsFormat": "decimal",
    }, timeout=30)
    if resp.status_code != 200:
        try:
            err = resp.json().get("message", resp.text)
        except Exception:
            err = resp.text
        return {}, f"HTTP {resp.status_code}: {err}"

    events = resp.json()
    fixtures = {}
    with open(FIXTURES_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fixtures[(row["home_team"], row["away_team"])] = row

    rows_by_match: dict[str, list[dict]] = {}
    for event in events:
        try:
            home = normalize_team_name(event["home_team"])
            away = normalize_team_name(event["away_team"])
        except KeyError:
            continue  # a team name we don't recognize -- skip rather than guess
        fx = fixtures.get((home, away))
        if fx is None:
            continue

        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                home_odds = outcomes.get(event["home_team"])
                away_odds = outcomes.get(event["away_team"])
                draw_odds = outcomes.get("Draw")
                if home_odds is None or away_odds is None or draw_odds is None:
                    continue
                rows_by_match.setdefault(fx["match_id"], []).append({
                    "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
                    "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
                    "bookmaker": bm.get("title", bm.get("key", "")), "market_type": "1X2",
                    "opening_home_odds": "", "opening_draw_odds": "", "opening_away_odds": "",
                    "current_home_odds": home_odds, "current_draw_odds": draw_odds, "current_away_odds": away_odds,
                    "closing_home_odds": "", "closing_draw_odds": "", "closing_away_odds": "",
                    "over_2_5_odds": "", "under_2_5_odds": "", "btts_yes_odds": "", "btts_no_odds": "",
                    "odds_snapshot_type": "current", "time_to_kickoff_hours": "", "odds_format": "decimal",
                    "odds_timestamp": bm.get("last_update", fetch_ts), "source_name": SOURCE_NAME,
                    "source_url_or_page_title": ODDS_API_URL, "is_example": False, "is_real_data": True,
                    "data_status": "live", "collection_date": fetch_ts[:10],
                    "notes": "Real current decimal odds from The Odds API. Opening/closing snapshots are not "
                             "available on the free tier and are intentionally left blank.",
                })
    return rows_by_match, None


def main() -> None:
    fetch_ts = now_utc_iso()
    with open(FIXTURES_PATH, newline="", encoding="utf-8") as f:
        fixtures = list(csv.DictReader(f))

    if not ODDS_API_KEY:
        print("ODDS_API_KEY not set (see .env.example) -- writing honest unavailable sentinel rows for all fixtures.")
        rows = [sentinel_row(fx, fetch_ts, SENTINEL_NOTE) for fx in fixtures]
        real_count = 0
    else:
        print(f"ODDS_API_KEY configured -- fetching live EPL h2h odds from {ODDS_API_URL} ...")
        rows_by_match, error = fetch_real_odds(fetch_ts)
        if error:
            print(f"WARNING: The Odds API request failed ({error}) -- falling back to unavailable sentinel rows. "
                  f"This is not a fabrication risk: we simply don't overwrite real odds with fake ones on failure.")
            rows = [sentinel_row(fx, fetch_ts, f"API request failed: {error}") for fx in fixtures]
            real_count = 0
        else:
            rows = []
            real_count = 0
            for fx in fixtures:
                match_rows = rows_by_match.get(fx["match_id"])
                if match_rows:
                    rows.extend(match_rows)
                    real_count += len(match_rows)
                else:
                    rows.append(sentinel_row(fx, fetch_ts, UNCOVERED_NOTE))
            print(f"Got real odds for {len(rows_by_match)} fixtures ({real_count} bookmaker rows); "
                  f"{len(fixtures) - len(rows_by_match)} fixtures have no market posted yet.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows ({real_count} real) to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_2026_27_real_odds",
        # Same rule as sentinel_row(): only claim the real source name if
        # real rows were actually obtained, not just because a key was set.
        source_name=SOURCE_NAME if real_count > 0 else "none_available",
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=real_count > 0,
        notes=f"{real_count} real bookmaker rows; rest are honest unavailable sentinels.",
    )


if __name__ == "__main__":
    main()
