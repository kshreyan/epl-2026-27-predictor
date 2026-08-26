"""Validates every raw data file against its required schema (spec
section 5) and basic integrity rules: correct columns present, no
duplicate match_id, expected row counts, allowed enum values.

Run: python -m src.data_validation.validate_raw_data
Exits non-zero if any check fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_validation.schema_definitions import (  # noqa: E402
    ALLOWED_AVAILABILITY_STATUS,
    ALLOWED_FIXTURE_STATUS,
    ALLOWED_ISSUE_TYPE,
    ALLOWED_ODDS_SNAPSHOT_TYPE,
    RAW_FILE_SCHEMAS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"


def validate_file(filename: str, expected_columns: list[str], expected_rows: int | None) -> list[str]:
    errors = []
    path = RAW_DIR / filename
    if not path.exists():
        return [f"{filename}: file does not exist"]

    df = pd.read_csv(path)
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"{filename}: missing required columns: {sorted(missing_cols)}")

    if expected_rows is not None and len(df) != expected_rows:
        errors.append(f"{filename}: expected {expected_rows} rows, found {len(df)}")

    if filename == "epl_2026_27_real_odds.csv":
        # match_id legitimately repeats here: one row per (match_id,
        # bookmaker, market_type) -- that combination is the real key.
        if {"match_id", "bookmaker", "market_type"}.issubset(df.columns):
            key_cols = ["match_id", "bookmaker", "market_type"]
            dupe_count = df[key_cols].dropna(subset=["match_id"]).duplicated().sum()
            if dupe_count > 0:
                errors.append(f"{filename}: {dupe_count} duplicate (match_id, bookmaker, market_type) rows")
    elif "match_id" in df.columns and df["match_id"].notna().any():
        dupes = df["match_id"].dropna()
        dupe_count = dupes.duplicated().sum()
        if dupe_count > 0:
            errors.append(f"{filename}: {dupe_count} duplicate match_id values")

    if filename == "epl_2026_27_fixtures.csv" and "status" in df.columns:
        bad_status = set(df["status"].dropna().unique()) - ALLOWED_FIXTURE_STATUS
        if bad_status:
            errors.append(f"{filename}: unexpected status values: {bad_status}")
        home_away_clash = (df["home_team"] == df["away_team"]).sum()
        if home_away_clash:
            errors.append(f"{filename}: {home_away_clash} rows with home_team == away_team")

    if filename == "epl_2026_27_injury_suspension.csv" and "availability_status" in df.columns:
        bad_avail = set(df["availability_status"].dropna().unique()) - ALLOWED_AVAILABILITY_STATUS
        if bad_avail:
            errors.append(f"{filename}: unexpected availability_status values: {bad_avail}")
        bad_issue = set(df["issue_type"].dropna().unique()) - ALLOWED_ISSUE_TYPE
        if bad_issue:
            errors.append(f"{filename}: unexpected issue_type values: {bad_issue}")

    if filename == "epl_2026_27_real_odds.csv" and "odds_snapshot_type" in df.columns:
        bad_snap = set(df["odds_snapshot_type"].dropna().unique()) - ALLOWED_ODDS_SNAPSHOT_TYPE
        if bad_snap:
            errors.append(f"{filename}: unexpected odds_snapshot_type values: {bad_snap}")

    if "is_real_data" in df.columns and "data_status" in df.columns:
        real_but_unavailable = df[(df["is_real_data"] == True) & (df["data_status"] == "unavailable")]  # noqa: E712
        if len(real_but_unavailable) > 0:
            errors.append(f"{filename}: {len(real_but_unavailable)} rows marked is_real_data=True but data_status=unavailable (contradiction)")

    if "is_real_data" in df.columns and "source_name" in df.columns:
        # A named, specific source next to is_real_data=False misleadingly
        # implies a real fetch happened for that row -- caught once in
        # src/data_collection/collect_odds.py (an API-error fallback path
        # left the real source name on sentinel rows) and generalized into
        # a standing check here so it can't recur in any collector.
        not_real = df[df["is_real_data"] == False]  # noqa: E712
        mislabeled = not_real[not_real["source_name"] != "none_available"]
        if len(mislabeled) > 0:
            errors.append(
                f"{filename}: {len(mislabeled)} rows have is_real_data=False but source_name != "
                f"'none_available' ({sorted(mislabeled['source_name'].unique())[:5]}) -- a non-real row "
                f"must not carry a specific source name"
            )

    return errors


def main() -> int:
    all_errors = []
    for filename, (columns, expected_rows) in RAW_FILE_SCHEMAS.items():
        errors = validate_file(filename, columns, expected_rows)
        all_errors.extend(errors)
        status = "OK" if not errors else "FAILED"
        print(f"[{status}] {filename}")
        for e in errors:
            print(f"    - {e}")

    if all_errors:
        print(f"\n{len(all_errors)} validation error(s) found.")
        return 1
    print("\nAll raw data files pass schema validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
