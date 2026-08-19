"""Match-level 1X2 odds collector for 2026-27 (spec section 5.7's
per-fixture counterpart to collect_outright_odds.py).

No live match-odds feed is connected to this pipeline (see
`collect_real_odds.py`/the-odds-api.com integration, which needs a
user-supplied API key). This script writes explicitly-flagged
unavailable rows per fixture rather than inventing odds -- **except**
for any match_id that already carries a real, manually-entered
snapshot (`data_status == "real_snapshot"`): those rows are preserved
as-is on every re-run, never silently overwritten back to a sentinel.

Run: python -m src.data_collection.collect_match_odds
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_match_odds.csv"

OUTPUT_COLUMNS = [
    "match_id", "home_team", "away_team", "bookmaker",
    "home_odds", "draw_odds", "away_odds",
    "home_implied_probability_raw", "draw_implied_probability_raw", "away_implied_probability_raw",
    "home_implied_probability_no_vig", "draw_implied_probability_no_vig", "away_implied_probability_no_vig",
    "odds_timestamp", "source_name", "source_url_or_page_title",
    "is_example", "is_real_data", "data_status", "collection_date", "notes",
]

NOTE = (
    "No live match-odds feed is connected to this pipeline (see collect_real_odds.py -- "
    "needs a user-supplied ODDS_API_KEY). Match-level benchmarking against a real market "
    "is unavailable for this fixture until a real snapshot is manually logged; do not use "
    "these rows to influence predictions."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    fixtures = pd.read_csv(FIXTURES_PATH)

    real_rows_by_id = {}
    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH, dtype=str, keep_default_na=False)
        real_existing = existing[existing["data_status"] == "real_snapshot"]
        real_rows_by_id = {row["match_id"]: row.to_dict() for _, row in real_existing.iterrows()}

    rows = []
    for _, fx in fixtures.iterrows():
        match_id = fx["match_id"]
        if match_id in real_rows_by_id:
            rows.append(real_rows_by_id[match_id])
            continue
        rows.append({
            "match_id": match_id, "home_team": fx["home_team"], "away_team": fx["away_team"],
            "bookmaker": "", "home_odds": "", "draw_odds": "", "away_odds": "",
            "home_implied_probability_raw": "", "draw_implied_probability_raw": "", "away_implied_probability_raw": "",
            "home_implied_probability_no_vig": "", "draw_implied_probability_no_vig": "", "away_implied_probability_no_vig": "",
            "odds_timestamp": fetch_ts, "source_name": "none_available", "source_url_or_page_title": "",
            "is_example": False, "is_real_data": False, "data_status": "unavailable",
            "collection_date": fetch_ts[:10], "notes": NOTE,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    n_real = len(real_rows_by_id)
    n_sentinel = len(rows) - n_real
    print(f"Wrote {len(rows)} match-odds rows to {OUTPUT_PATH} "
          f"({n_real} preserved real_snapshot rows, {n_sentinel} unavailable sentinel rows)")

    log_data_version(
        dataset_name="epl_2026_27_match_odds",
        source_name="none_available" if n_real == 0 else "mixed: real_snapshot + none_available",
        source_timestamp=fetch_ts, row_count=len(rows), is_real_data=n_real > 0, notes=NOTE,
    )


if __name__ == "__main__":
    main()
