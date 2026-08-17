"""Match-odds (1X2 + totals + BTTS) collector for the 2026-27 season.

No live/current bookmaker odds feed is connected to this pipeline (that
requires a paid odds-API subscription). Per spec section 5.6 / section
17 ("If market odds are unavailable, use model-only mode"), this
script writes one `data_status=unavailable` row per real fixture (so
match predictions can still join on `match_id`) rather than inventing
odds. `market_available` must be derived as False from these rows.

Run: python -m src.data_collection.collect_odds
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv"

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

NOTE = (
    "No live odds-API subscription is connected to this pipeline. Row exists "
    "only to preserve a match_id join for downstream code; market_available "
    "must be derived as False. Model predictions run in model-only mode "
    "until a real odds feed is wired in."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    with open(FIXTURES_PATH, newline="", encoding="utf-8") as f:
        fixtures = list(csv.DictReader(f))

    rows = []
    for fx in fixtures:
        rows.append({
            "match_id": fx["match_id"],
            "season": fx["season"],
            "matchweek": fx["matchweek"],
            "date": fx["date"],
            "kickoff_utc": fx["kickoff_utc"],
            "home_team": fx["home_team"],
            "away_team": fx["away_team"],
            "bookmaker": "",
            "market_type": "1X2",
            "opening_home_odds": "", "opening_draw_odds": "", "opening_away_odds": "",
            "current_home_odds": "", "current_draw_odds": "", "current_away_odds": "",
            "closing_home_odds": "", "closing_draw_odds": "", "closing_away_odds": "",
            "over_2_5_odds": "", "under_2_5_odds": "", "btts_yes_odds": "", "btts_no_odds": "",
            "odds_snapshot_type": "unknown",
            "time_to_kickoff_hours": "",
            "odds_format": "decimal",
            "odds_timestamp": fetch_ts,
            "source_name": "none_available",
            "source_url_or_page_title": "",
            "is_example": False,
            "is_real_data": False,
            "data_status": "unavailable",
            "collection_date": fetch_ts[:10],
            "notes": NOTE,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} unavailable-odds sentinel rows to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_2026_27_real_odds",
        source_name="none_available",
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=False,
        notes=NOTE,
    )


if __name__ == "__main__":
    main()
