import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
PREDICTIONS_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"


def test_historical_matches_are_not_in_the_future():
    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    assert (df["date"] < pd.Timestamp.now(tz=None).normalize() + pd.Timedelta(days=1)).all()


def test_fixture_source_timestamp_precedes_kickoff():
    df = pd.read_csv(FIXTURES_PATH, parse_dates=["source_timestamp", "kickoff_utc"], date_format="ISO8601")
    assert (df["source_timestamp"] <= df["kickoff_utc"]).all()


@pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")
def test_predictions_generated_before_kickoff():
    df = pd.read_csv(PREDICTIONS_PATH, parse_dates=["generated_at", "kickoff_utc"], date_format="ISO8601")
    assert (df["generated_at"] <= df["kickoff_utc"]).all(), (
        "A prediction's generated_at timestamp must never be after that match's kickoff -- "
        "this is the core leakage-safety check for preseason_mode predictions."
    )


@pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")
def test_scheduled_matches_have_no_actual_result():
    df = pd.read_csv(PREDICTIONS_PATH)
    scheduled = df[df["status"] == "scheduled"]
    assert scheduled["actual_home_goals"].isna().all()
    assert scheduled["actual_away_goals"].isna().all()
