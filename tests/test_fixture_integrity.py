import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import all_league_ids, league_path, load_league_config  # noqa: E402
from src.utils.team_names import CANONICAL_TEAMS, EPL_2026_27_CLUBS  # noqa: E402

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


# Generalized versions of the same checks above, parametrized over every
# league registered in config/leagues.yaml (not just EPL's hardcoded 380/
# 38/10) -- skips a league whose fixture file hasn't been collected yet
# rather than failing, since collect_fixtures.py is a one-time bootstrap
# step run manually per league, not part of every test run.
def _fixtures_path_for(league_id: str) -> Path:
    return REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")


def _skip_reason(league_id: str) -> str | None:
    if not _fixtures_path_for(league_id).exists():
        return f"{league_id}: fixtures not collected yet -- run collect_fixtures.py --league {league_id}"
    return None


@pytest.mark.parametrize("league_id", all_league_ids())
def test_any_league_has_correct_fixture_count_and_matches_per_team(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    cfg = load_league_config(league_id)
    df = pd.read_csv(_fixtures_path_for(league_id))
    expected_fixtures = cfg.n_teams * (cfg.n_teams - 1)
    assert len(df) == expected_fixtures
    assert df["match_id"].duplicated().sum() == 0
    assert (df["home_team"] == df["away_team"]).sum() == 0

    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    assert (counts == 2 * (cfg.n_teams - 1)).all()

    teams = set(df["home_team"]) | set(df["away_team"])
    assert len(teams) == cfg.n_teams
    # Every real 2026-27 club name must be one this league's canonical
    # registry actually knows about -- catches a team-alias gap before
    # it ever reaches normalize_team_name() in production.
    known = set(CANONICAL_TEAMS[league_id].keys())
    assert teams <= known, f"{league_id}: unrecognized team(s) in fixture list: {teams - known}"

    n_matchweeks = 2 * (cfg.n_teams - 1)
    matches_per_matchweek = cfg.n_teams // 2
    mw_counts = df["matchweek"].value_counts()
    assert set(mw_counts.index) == set(range(1, n_matchweeks + 1))
    assert (mw_counts == matches_per_matchweek).all()
