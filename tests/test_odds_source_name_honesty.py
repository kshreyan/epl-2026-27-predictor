"""Regression test for a real bug: an earlier version of
src/data_collection/collect_odds.py set source_name to the real
provider name ("the-odds-api.com") on sentinel rows whenever
ODDS_API_KEY was merely *configured*, even if the actual API request
failed (e.g. an invalid key) and zero real rows were obtained. A named
source next to is_real_data=False misleadingly implies a real fetch
happened for that row. Caught during review; fixed in collect_odds.py
and generalized into a standing check in validate_raw_data.py -- this
test exercises the specific failure mode that caused it.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection.collect_odds import sentinel_row  # noqa: E402
from src.data_validation.validate_raw_data import validate_file  # noqa: E402

RAW_ODDS_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv"


def test_sentinel_row_always_uses_none_available_source_name():
    fx = {"match_id": "X", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
          "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Arsenal", "away_team": "Coventry City"}
    row = sentinel_row(fx, "2026-08-18T00:00:00+00:00", "any note")
    assert row["source_name"] == "none_available"
    assert row["is_real_data"] is False


@pytest.mark.skipif(not RAW_ODDS_PATH.exists(), reason="run the odds collector first")
def test_real_odds_file_never_names_a_source_on_a_non_real_row():
    df = pd.read_csv(RAW_ODDS_PATH)
    not_real = df[df["is_real_data"] == False]  # noqa: E712
    assert (not_real["source_name"] == "none_available").all()


def test_validator_catches_a_mislabeled_sentinel_row(tmp_path, monkeypatch):
    """Directly reproduces the bug: a sentinel row with is_real_data=False
    but a named source, and confirms validate_file() flags it."""
    import src.data_validation.validate_raw_data as validate_mod
    bad_df = pd.DataFrame([{
        "match_id": "X", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
        "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Arsenal", "away_team": "Coventry City",
        "bookmaker": "", "market_type": "1X2",
        "opening_home_odds": "", "opening_draw_odds": "", "opening_away_odds": "",
        "current_home_odds": "", "current_draw_odds": "", "current_away_odds": "",
        "closing_home_odds": "", "closing_draw_odds": "", "closing_away_odds": "",
        "over_2_5_odds": "", "under_2_5_odds": "", "btts_yes_odds": "", "btts_no_odds": "",
        "odds_snapshot_type": "unknown", "time_to_kickoff_hours": "", "odds_format": "decimal",
        "odds_timestamp": "2026-08-18T00:00:00+00:00",
        "source_name": "the-odds-api.com",  # the bug: a real-looking source name
        "source_url_or_page_title": "", "is_example": False, "is_real_data": False,
        "data_status": "unavailable", "collection_date": "2026-08-18", "notes": "",
    }])
    bad_path = tmp_path / "epl_2026_27_real_odds.csv"
    bad_df.to_csv(bad_path, index=False)
    monkeypatch.setattr(validate_mod, "RAW_DIR", tmp_path)

    from src.data_validation.schema_definitions import RAW_FILE_SCHEMAS
    columns, expected_rows = RAW_FILE_SCHEMAS["epl_2026_27_real_odds.csv"]
    errors = validate_file("epl_2026_27_real_odds.csv", columns, None)  # None: this fixture has 1 row, not 380
    assert any("source_name" in e for e in errors)
