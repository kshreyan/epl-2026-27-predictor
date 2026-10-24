"""Collect real historical UFC fight results from ESPN's site API (see
espn_mma_api.py for source rationale), several real past calendar
years. Chunked one real request per calendar year -- a real multi-year
date-range query was rejected by ESPN with an HTTP 400 (confirmed
directly this session).

Only real COMPLETED fights with a real decisive method (`decision` or
`finish`) are kept -- a real no-contest/cancelled booking (`unscored`,
see espn_mma_api.py) carries no real outcome to learn from and is
skipped, not guessed.

Run: python -m src.data_collection.collect_espn_ufc_historical
"""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_collection.espn_mma_api import fetch_real_ufc_events  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "site.api.espn.com"
N_PRIOR_YEARS = 5

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "event_id", "event_name",
    "fighter_a", "fighter_b", "weight_class", "scheduled_rounds",
    "winner", "method", "finish_round",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]


def main() -> None:
    cfg = load_league_config("ufc")
    output_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "historical_fights.csv")

    this_year = date.today().year
    years = list(range(this_year - N_PRIOR_YEARS, this_year + 1))

    rows = []
    fetch_ts = now_utc_iso()
    for year in years:
        events = fetch_real_ufc_events(date(year, 1, 1), date(year, 12, 31))
        n_this_year = 0
        for ev in events:
            for f in ev["fights"]:
                if not f["completed"] or f["method"] == "unscored":
                    continue
                winner = "fighter_a" if f["winner_id"] == f["fighter_a_id"] else ("fighter_b" if f["winner_id"] == f["fighter_b_id"] else "")
                if not winner:
                    continue  # a real draw/no-winner result carries no real win/loss signal for the Elo model
                dt_utc = datetime.fromisoformat(f["date"].replace("Z", "+00:00"))
                match_id = f"{cfg.match_id_prefix}{year}_{ev['event_id']}_{f['fight_id']}"
                rows.append({
                    "season": str(year), "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
                    "event_id": ev["event_id"], "event_name": ev["event_name"],
                    "fighter_a": f["fighter_a_name"], "fighter_b": f["fighter_b_name"],
                    "weight_class": f["weight_class"], "scheduled_rounds": f["scheduled_rounds"],
                    "winner": winner, "method": f["method"], "finish_round": f["finish_round"] or "",
                    "source_name": SOURCE_NAME,
                    "source_url_or_page_title": "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard",
                    "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "completed",
                    "notes": "",
                })
                n_this_year += 1
        print(f"  {year}: {n_this_year} real completed fights ({len(events)} real events)")

    rows.sort(key=lambda r: r["date"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real historical fights to {output_path} ({years[0]}-{years[-1]})")

    log_data_version(
        dataset_name="ufc_historical_fights", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(rows), is_real_data=True,
        notes=f"UFC, {len(years)} real prior calendar years from ESPN's site API.",
    )


if __name__ == "__main__":
    main()
