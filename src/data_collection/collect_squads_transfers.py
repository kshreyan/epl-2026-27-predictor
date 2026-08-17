"""Squad/transfer data collector for the 2026-27 season.

No free, reliably-licensed, per-player source (transfer fees, minutes,
xG/xA, market values) is available to this pipeline. Per the project's
data-honesty rules (spec section 2), we do NOT fabricate player rows.

This script writes one `data_status=unavailable` sentinel row per club
(so downstream joins on `team` still work and missingness is visible
in the data itself, not just in a report) and is structured so a real
feed (a licensed data vendor, or manually curated CSV) can replace the
sentinel rows without changing the schema or any downstream code.

Run: python -m src.data_collection.collect_squads_transfers
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_squads_transfers.csv"

OUTPUT_COLUMNS = [
    "team", "player_name", "position", "age", "nationality", "squad_status",
    "transfer_type", "from_club", "to_club", "fee_reported", "estimated_market_value",
    "minutes_last_season", "starts_last_season", "goals_last_season", "assists_last_season",
    "xg_last_season", "xa_last_season", "npxg_last_season",
    "defensive_actions_last_season", "progressive_actions_last_season",
    "set_piece_role", "penalty_taker_flag", "goalkeeper_psxg_minus_goals_allowed_if_gk",
    "importance_score", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

NOTE = (
    "No verified, licensed per-player squad/transfer feed is connected to "
    "this pipeline. This sentinel row exists so `team` joins still work; "
    "it must not be treated as a real player record. Replace with a real "
    "feed before using squad/transfer features for predictions."
)


def main() -> None:
    fetch_ts = now_utc_iso()
    rows = []
    for team in EPL_2026_27_CLUBS:
        rows.append({
            "team": team,
            "player_name": "",
            "position": "",
            "age": "",
            "nationality": "",
            "squad_status": "unknown",
            "transfer_type": "",
            "from_club": "",
            "to_club": "",
            "fee_reported": "",
            "estimated_market_value": "",
            "minutes_last_season": "",
            "starts_last_season": "",
            "goals_last_season": "",
            "assists_last_season": "",
            "xg_last_season": "",
            "xa_last_season": "",
            "npxg_last_season": "",
            "defensive_actions_last_season": "",
            "progressive_actions_last_season": "",
            "set_piece_role": "",
            "penalty_taker_flag": "",
            "goalkeeper_psxg_minus_goals_allowed_if_gk": "",
            "importance_score": "",
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

    print(f"Wrote {len(rows)} sentinel rows (all flagged unavailable) to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_2026_27_squads_transfers",
        source_name="none_available",
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=False,
        notes=NOTE,
    )


if __name__ == "__main__":
    main()
