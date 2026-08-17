"""Collect real EPL historical match results, 2014/15-2025/26.

Source: football-data.co.uk per-season E0.csv files (free, public,
direct CSV download). This source provides goals, shots, cards,
referee, and historical Bet365 1X2 odds. It does NOT provide xG,
PPDA, possession, big-chances, set-piece-xG, or attendance for these
seasons -- those columns are left blank and explicitly flagged
`data_status=unavailable` in `notes`, per the project's no-fabrication
rule (see PLAN.md / project spec section 2 and 5.2).

Run: python -m src.data_collection.collect_historical_results
"""
from __future__ import annotations

import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CACHE_DIR = REPO_ROOT / "data" / "external" / "football_data_co_uk"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"

SOURCE_NAME = "football-data.co.uk"
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"

# 2014/15 through 2025/26
SEASON_CODES = [
    "1415", "1516", "1617", "1718", "1819", "1920",
    "2021", "2122", "2223", "2324", "2425", "2526",
]

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team",
    "home_goals", "away_goals", "result",
    "home_xg", "away_xg",
    "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession",
    "home_ppda", "away_ppda",
    "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg",
    "home_red_cards", "away_red_cards",
    "referee", "stadium", "attendance",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

UNAVAILABLE_NOTE = (
    "Advanced metrics (xG, possession, PPDA, big_chances, set_piece_xg), "
    "stadium, and attendance are not published by football-data.co.uk and "
    "are intentionally left blank rather than estimated."
)


def season_code_to_label(code: str) -> str:
    start = "20" + code[:2]
    end = code[2:]
    return f"{start}-{end}"


def download_season_csv(code: str) -> str:
    cache_path = RAW_CACHE_DIR / f"E0_{code}.csv"
    url = BASE_URL.format(code=code)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    RAW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    return resp.text


def parse_season(code: str, csv_text: str, source_timestamp: str) -> list[dict]:
    season_label = season_code_to_label(code)
    rows_out = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for i, row in enumerate(reader):
        home_raw = (row.get("HomeTeam") or "").strip()
        away_raw = (row.get("AwayTeam") or "").strip()
        date_raw = (row.get("Date") or "").strip()
        if not home_raw or not away_raw or not date_raw:
            continue  # trailing blank rows in some source files

        home_team = normalize_team_name(home_raw)
        away_team = normalize_team_name(away_raw)

        try:
            date_obj = datetime.strptime(date_raw, "%d/%m/%Y")
        except ValueError:
            date_obj = datetime.strptime(date_raw, "%d/%m/%y")
        date_iso = date_obj.strftime("%Y-%m-%d")

        ftr = (row.get("FTR") or "").strip()
        result_map = {"H": "home_win", "D": "draw", "A": "away_win"}

        match_id = f"EPLHIST_{code}_{i+1:03d}_{home_team.replace(' ', '')}_{away_team.replace(' ', '')}"

        def num(field: str):
            v = (row.get(field) or "").strip()
            return v if v != "" else ""

        rows_out.append({
            "season": season_label,
            "match_id": match_id,
            "date": date_iso,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": num("FTHG"),
            "away_goals": num("FTAG"),
            "result": result_map.get(ftr, "unknown"),
            "home_xg": "",
            "away_xg": "",
            "home_shots": num("HS"),
            "away_shots": num("AS"),
            "home_shots_on_target": num("HST"),
            "away_shots_on_target": num("AST"),
            "home_possession": "",
            "away_possession": "",
            "home_ppda": "",
            "away_ppda": "",
            "home_big_chances": "",
            "away_big_chances": "",
            "home_set_piece_xg": "",
            "away_set_piece_xg": "",
            "home_red_cards": num("HR"),
            "away_red_cards": num("AR"),
            "referee": (row.get("Referee") or "").strip(),
            "stadium": "",
            "attendance": "",
            "source_name": SOURCE_NAME,
            "source_url_or_page_title": BASE_URL.format(code=code),
            "source_timestamp": source_timestamp,
            "is_real_data": True,
            "data_status": "completed",
            "notes": UNAVAILABLE_NOTE,
        })
    return rows_out


def main() -> None:
    all_rows: list[dict] = []
    fetch_ts = now_utc_iso()
    for code in SEASON_CODES:
        print(f"Downloading EPL {season_code_to_label(code)} from {SOURCE_NAME} ...")
        csv_text = download_season_csv(code)
        season_rows = parse_season(code, csv_text, fetch_ts)
        print(f"  -> {len(season_rows)} matches")
        all_rows.extend(season_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} historical matches to {OUTPUT_PATH}")

    log_data_version(
        dataset_name="epl_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=fetch_ts,
        row_count=len(all_rows),
        is_real_data=True,
        notes=f"Seasons {SEASON_CODES[0]}-{SEASON_CODES[-1]}; " + UNAVAILABLE_NOTE,
    )


if __name__ == "__main__":
    main()
