"""Tests the live-results fetcher's parsing/matching logic with
synthetic CSV text (mirroring football-data.co.uk's real column
format) against a small synthetic fixtures table -- never touches the
real fixtures file or makes a real network call."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection.fetch_live_results import parse_live_results  # noqa: E402

FIXTURES = pd.DataFrame([
    {"match_id": "m1", "matchweek": 1, "home_team": "Arsenal", "away_team": "Coventry City", "kickoff_utc": "2026-08-21T19:00:00+00:00"},
    {"match_id": "m2", "matchweek": 1, "home_team": "Hull City", "away_team": "Manchester United", "kickoff_utc": "2026-08-22T11:30:00+00:00"},
])

CSV_HEADER = "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,Referee\n"


def test_parses_completed_matches_and_maps_to_real_match_id():
    csv_text = CSV_HEADER + "E0,21/08/2026,19:00,Arsenal,Coventry,2,0,H,A Taylor\n"
    results = parse_live_results(csv_text, FIXTURES)
    assert len(results) == 1
    assert results.iloc[0]["match_id"] == "m1"
    assert results.iloc[0]["home_goals"] == 2
    assert results.iloc[0]["away_goals"] == 0
    assert results.iloc[0]["source_name"] == "football-data.co.uk"


def test_skips_not_yet_played_matches():
    # FTHG/FTAG blank -- a fixture in the CSV that hasn't kicked off yet.
    csv_text = CSV_HEADER + "E0,22/08/2026,11:30,Hull,Man United,,,,\n"
    results = parse_live_results(csv_text, FIXTURES)
    assert results.empty


def test_raises_on_unrecognized_team_name_rather_than_guessing():
    csv_text = CSV_HEADER + "E0,21/08/2026,19:00,Not A Real Team,Coventry,1,0,H,A Taylor\n"
    with pytest.raises(KeyError):
        parse_live_results(csv_text, FIXTURES)


def test_raises_if_completed_result_has_no_matching_fixture():
    # A real, recognized team pairing but one that simply isn't in this
    # season's fixture list -- a real data-integrity signal, not
    # something to silently drop.
    csv_text = CSV_HEADER + "E0,21/08/2026,19:00,Arsenal,Liverpool,3,1,H,A Taylor\n"
    with pytest.raises(ValueError, match="no matching fixture"):
        parse_live_results(csv_text, FIXTURES)


def test_parses_multiple_completed_matches_in_one_call():
    csv_text = (
        CSV_HEADER
        + "E0,21/08/2026,19:00,Arsenal,Coventry,2,0,H,A Taylor\n"
        + "E0,22/08/2026,11:30,Hull,Man United,0,3,A,M Oliver\n"
    )
    results = parse_live_results(csv_text, FIXTURES)
    assert len(results) == 2
    assert set(results["match_id"]) == {"m1", "m2"}
