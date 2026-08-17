"""Injury/suspension data collector for the 2026-27 season.

No free, reliably-verifiable live injury/suspension feed is connected
to this pipeline. Per spec section 5.5's own rule ("If no verified
report exists, create team-level unknown rows" and "missing injury
data must not be treated as fully healthy"), this script writes one
explicit team-level `availability_status=unknown` sentinel row per
club rather than fabricating player-level injury news or silently
omitting the file.

Run: python -m src.data_collection.collect_injuries
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_injury_suspension.csv"

OUTPUT_COLUMNS = [
    "match_id", "matchweek", "date", "team", "opponent", "player_name",
    "availability_status", "issue_type", "body_part_or_reason", "expected_return",
    "player_importance", "starter_probability_if_fit", "minutes_expectation_if_fit",
    "impact_score", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

NOTE = (
    "No verified live injury/suspension feed is connected to this pipeline. "
    "This is a team-level 'unknown' sentinel, not a real report -- downstream "
    "features must set home/away_missing_injury_data_flag=True from this row "
    "and MUST NOT treat it as 'fully healthy'."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    rows = []
    for team in EPL_2026_27_CLUBS:
        rows.append({
            "match_id": "",
            "matchweek": "",
            "date": "",
            "team": team,
            "opponent": "",
            "player_name": "",
            "availability_status": "unknown",
            "issue_type": "unknown",
            "body_part_or_reason": "",
            "expected_return": "",
            "player_importance": "",
            "starter_probability_if_fit": "",
            "minutes_expectation_if_fit": "",
            "impact_score": "",
            "source_name": "none_available",
            "source_url_or_page_title": "",
            "source_timestamp": fetch_ts,
            "is_real_data": False,
            "data_status": "unavailable",
            "notes": NOTE,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} team-level unknown sentinel rows to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_2026_27_injury_suspension",
        source_name="none_available",
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=False,
        notes=NOTE,
    )


if __name__ == "__main__":
    main()
