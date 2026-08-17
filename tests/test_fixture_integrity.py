import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402

FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"


def load_fixtures() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_PATH)


def test_all_380_fixtures_present():
    df = load_fixtures()
    assert len(df) == 380


def test_no_duplicate_match_ids():
    df = load_fixtures()
    assert df["match_id"].duplicated().sum() == 0


def test_20_real_clubs_each_playing_38_matches():
    df = load_fixtures()
    teams = set(df["home_team"]) | set(df["away_team"])
    assert teams == set(EPL_2026_27_CLUBS)
    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    assert (counts == 38).all()


def test_no_team_plays_itself():
    df = load_fixtures()
    assert (df["home_team"] == df["away_team"]).sum() == 0


def test_each_team_plays_every_opponent_home_and_away():
    df = load_fixtures()
    pairs = set(zip(df["home_team"], df["away_team"]))
    for home in EPL_2026_27_CLUBS:
        for away in EPL_2026_27_CLUBS:
            if home == away:
                continue
            assert (home, away) in pairs, f"{home} vs {away} missing as a fixture"


def test_matchweeks_1_through_38_each_have_10_matches():
    df = load_fixtures()
    counts = df["matchweek"].value_counts()
    assert set(counts.index) == set(range(1, 39))
    assert (counts == 10).all()
