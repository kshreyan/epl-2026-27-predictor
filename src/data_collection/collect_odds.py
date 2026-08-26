"""Match-odds (1X2, spreads/Asian handicap, totals) collector for the
2026-27 season.

Uses The Odds API (https://the-odds-api.com/) when a real API key is
configured -- read from the `ODDS_API_KEY` environment variable (via a
local, gitignored `.env` file; see `.env.example`), never hardcoded,
never committed. Their terms permit using this data inside a broader
analytical dashboard (not reselling it as a standalone data product),
which is what this project does.

**Without a configured key, this script does exactly what it did
before**: writes one `data_status=unavailable` sentinel row per
(fixture, market_type) (spec section 5.6 / 17 "If market odds are
unavailable, use model-only mode"). `market_available` must be derived
as False from those rows.

**With a configured key**: fetches the current EPL h2h, spreads, and
totals markets (confirmed available via a real API call, 2026-08-26 --
`markets=h2h,spreads,totals`), writes one real row per (fixture,
bookmaker, market_type) actually returned, and leaves every
(fixture, market_type) combination the API doesn't cover yet
(bookmakers post different markets at different times before kickoff)
as the same honest sentinel row as before. Raw per-bookmaker decimal
odds/lines are written as returned; overround removal and cross-
bookmaker averaging happen downstream (`src/features/build_market_features.py`
for h2h; `src/models/market_blend_model.py` for the validated blends).

**BTTS (both teams to score) is not available from this or any other
connected source**, confirmed directly rather than assumed: The Odds
API's `/odds` endpoint returns `INVALID_MARKET` for `btts` on this
sport (tested 2026-08-26), and football-data.co.uk's historical files
(the source behind `data/external/football_data_co_uk/`) have no BTTS
column either (checked directly: no `BTS`/`BTTS`/`both` column exists
in any cached season file, only Asian Handicap and Over/Under 2.5
columns). The `btts_yes_odds`/`btts_no_odds` schema columns remain as
an honest, permanently-empty placeholder, not removed, so downstream
code has a stable column to check `market_available` against if a
BTTS-capable source is ever connected. The model's own BTTS prediction
(`src/models/scoreline_models.btts_probability`) is unaffected --
it never depended on a real market baseline existing.

Only `current_*_odds` / the single `_line` per market are ever
populated by this collector -- The Odds API's free tier does not
provide historical opening/closing snapshots, so `opening_*_odds` and
`closing_*_odds` stay blank + flagged, not estimated.

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
ODDS_API_MARKETS = "h2h,spreads,totals"  # btts is INVALID_MARKET on this endpoint for this sport -- confirmed, not guessed
SOURCE_NAME = "the-odds-api.com"
MARKET_TYPES = ["h2h", "spreads", "totals"]

OUTPUT_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team",
    "bookmaker", "market_type",
    "opening_home_odds", "opening_draw_odds", "opening_away_odds",
    "current_home_odds", "current_draw_odds", "current_away_odds",
    "closing_home_odds", "closing_draw_odds", "closing_away_odds",
    "spread_line", "home_spread_odds", "away_spread_odds",
    "total_line", "over_odds", "under_odds",
    "btts_yes_odds", "btts_no_odds",
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
    "The Odds API is configured and reachable, but has not yet posted this market for this fixture "
    "(bookmakers open different markets at different times before kickoff) -- genuinely unavailable, "
    "not a collector failure."
)

_BLANK_ODDS_FIELDS = {
    "opening_home_odds": "", "opening_draw_odds": "", "opening_away_odds": "",
    "current_home_odds": "", "current_draw_odds": "", "current_away_odds": "",
    "closing_home_odds": "", "closing_draw_odds": "", "closing_away_odds": "",
    "spread_line": "", "home_spread_odds": "", "away_spread_odds": "",
    "total_line": "", "over_odds": "", "under_odds": "",
    "btts_yes_odds": "", "btts_no_odds": "",
}


def sentinel_row(fx: dict, market_type: str, fetch_ts: str, note: str) -> dict:
    return {
        "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
        "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": fx["home_team"], "away_team": fx["away_team"],
        "bookmaker": "", "market_type": market_type,
        **_BLANK_ODDS_FIELDS,
        "odds_snapshot_type": "unknown", "time_to_kickoff_hours": "", "odds_format": "decimal",
        # source_name is ALWAYS "none_available" here, regardless of whether
        # ODDS_API_KEY is configured: is_real_data=False on every sentinel
        # row, and a populated source_name next to is_real_data=False would
        # misleadingly suggest a real fetch happened for this specific row.
        "odds_timestamp": fetch_ts, "source_name": "none_available",
        "source_url_or_page_title": "", "is_example": False, "is_real_data": False,
        "data_status": "unavailable", "collection_date": fetch_ts[:10], "notes": note,
    }


def fetch_real_odds(fetch_ts: str) -> tuple[dict[tuple[str, str], list[dict]], str | None]:
    """Returns ((match_id, market_type) -> list of real per-bookmaker row
    dicts, error_message_or_None)."""
    resp = requests.get(ODDS_API_URL, params={
        "apiKey": ODDS_API_KEY, "regions": "uk,us,eu", "markets": ODDS_API_MARKETS, "oddsFormat": "decimal",
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

    rows_by_key: dict[tuple[str, str], list[dict]] = {}
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
                market_type = market.get("key")
                if market_type not in MARKET_TYPES:
                    continue
                outcomes = market.get("outcomes", [])
                row = {
                    "match_id": fx["match_id"], "season": fx["season"], "matchweek": fx["matchweek"],
                    "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "home_team": home, "away_team": away,
                    # bm["key"] (e.g. "betfair_ex_uk" vs "betfair_ex_eu") is the
                    # real unique identifier -- two distinct bookmaker keys can
                    # share the same display title ("Betfair"), which produced
                    # genuine (match_id, bookmaker, market_type) duplicates when
                    # this used title alone (caught via validate_raw_data.py).
                    "bookmaker": bm.get("key", bm.get("title", "")), "market_type": market_type,
                    **_BLANK_ODDS_FIELDS,
                    "odds_snapshot_type": "current", "time_to_kickoff_hours": "", "odds_format": "decimal",
                    "odds_timestamp": bm.get("last_update", fetch_ts), "source_name": SOURCE_NAME,
                    "source_url_or_page_title": ODDS_API_URL, "is_example": False, "is_real_data": True,
                    "data_status": "live", "collection_date": fetch_ts[:10],
                    "notes": "Real current decimal odds from The Odds API. Opening/closing snapshots are not "
                             "available on the free tier and are intentionally left blank.",
                }

                if market_type == "h2h":
                    by_name = {o["name"]: o["price"] for o in outcomes}
                    home_odds, away_odds, draw_odds = by_name.get(event["home_team"]), by_name.get(event["away_team"]), by_name.get("Draw")
                    if home_odds is None or away_odds is None or draw_odds is None:
                        continue
                    row["current_home_odds"], row["current_draw_odds"], row["current_away_odds"] = home_odds, draw_odds, away_odds

                elif market_type == "spreads":
                    by_name = {o["name"]: o for o in outcomes}
                    home_o, away_o = by_name.get(event["home_team"]), by_name.get(event["away_team"])
                    if home_o is None or away_o is None:
                        continue
                    row["spread_line"], row["home_spread_odds"], row["away_spread_odds"] = home_o.get("point"), home_o.get("price"), away_o.get("price")

                elif market_type == "totals":
                    by_name = {o["name"]: o for o in outcomes}
                    over_o, under_o = by_name.get("Over"), by_name.get("Under")
                    if over_o is None or under_o is None:
                        continue
                    row["total_line"], row["over_odds"], row["under_odds"] = over_o.get("point"), over_o.get("price"), under_o.get("price")

                rows_by_key.setdefault((fx["match_id"], market_type), []).append(row)
    return rows_by_key, None


def main() -> None:
    fetch_ts = now_utc_iso()
    with open(FIXTURES_PATH, newline="", encoding="utf-8") as f:
        fixtures = list(csv.DictReader(f))

    if not ODDS_API_KEY:
        print("ODDS_API_KEY not set (see .env.example) -- writing honest unavailable sentinel rows for all fixtures.")
        rows = [sentinel_row(fx, mt, fetch_ts, SENTINEL_NOTE) for fx in fixtures for mt in MARKET_TYPES]
        real_count = 0
    else:
        print(f"ODDS_API_KEY configured -- fetching live EPL {ODDS_API_MARKETS} odds from {ODDS_API_URL} ...")
        rows_by_key, error = fetch_real_odds(fetch_ts)
        if error:
            print(f"WARNING: The Odds API request failed ({error}) -- falling back to unavailable sentinel rows. "
                  f"This is not a fabrication risk: we simply don't overwrite real odds with fake ones on failure.")
            rows = [sentinel_row(fx, mt, fetch_ts, f"API request failed: {error}") for fx in fixtures for mt in MARKET_TYPES]
            real_count = 0
        else:
            rows = []
            real_count = 0
            covered_fixtures = set()
            for fx in fixtures:
                for mt in MARKET_TYPES:
                    match_rows = rows_by_key.get((fx["match_id"], mt))
                    if match_rows:
                        rows.extend(match_rows)
                        real_count += len(match_rows)
                        covered_fixtures.add(fx["match_id"])
                    else:
                        rows.append(sentinel_row(fx, mt, fetch_ts, UNCOVERED_NOTE))
            print(f"Got real odds for {len(covered_fixtures)} fixtures ({real_count} bookmaker/market rows across "
                  f"{ODDS_API_MARKETS}); {len(fixtures) - len(covered_fixtures)} fixtures have no market posted yet.")

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
        notes=f"{real_count} real bookmaker/market rows; rest are honest unavailable sentinels.",
    )


if __name__ == "__main__":
    main()
