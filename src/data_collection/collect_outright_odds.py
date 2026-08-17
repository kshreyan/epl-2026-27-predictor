"""Season-outright odds (title/top-4/relegation/...) collector for 2026-27.

No live outright-odds feed is connected to this pipeline. Per spec
section 5.7, this script writes explicitly-flagged unavailable rows
per team/market_type rather than inventing odds.

Run: python -m src.data_collection.collect_outright_odds
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_outright_odds.csv"

OUTPUT_COLUMNS = [
    "team", "market_type", "bookmaker", "odds", "implied_probability_raw",
    "implied_probability_no_vig", "odds_timestamp", "source_name",
    "source_url_or_page_title", "is_example", "is_real_data", "data_status",
    "collection_date", "notes",
]

MARKET_TYPES = [
    "title_winner", "top_4", "top_5", "relegation", "top_half", "bottom_half", "golden_boot",
]

NOTE = (
    "No live outright-odds feed is connected to this pipeline. Season-level "
    "benchmarking against market outrights is unavailable until a real feed "
    "is wired in; do not use these rows to influence match-level predictions."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    rows = []
    for team in EPL_2026_27_CLUBS:
        for market_type in MARKET_TYPES:
            rows.append({
                "team": team,
                "market_type": market_type,
                "bookmaker": "",
                "odds": "",
                "implied_probability_raw": "",
                "implied_probability_no_vig": "",
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

    print(f"Wrote {len(rows)} unavailable outright-odds sentinel rows to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_2026_27_outright_odds",
        source_name="none_available",
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=False,
        notes=NOTE,
    )


if __name__ == "__main__":
    main()
