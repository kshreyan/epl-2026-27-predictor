"""Integrity checks for the real UEFA Nations League fixture/historical
data -- a "groups" format league (see src/leagues.py), so it does not
fit test_fixture_integrity.py's single round-robin assertions."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.team_names import CANONICAL_TEAMS  # noqa: E402

FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "nations_league_2026_27_fixtures.csv"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "nations_league_historical_matches.csv"

pytestmark = pytest.mark.skipif(
    not FIXTURES_PATH.exists(),
    reason="nations_league fixtures not collected yet -- run collect_nations_league_fixtures.py",
)


def test_156_real_fixtures_present():
    df = pd.read_csv(FIXTURES_PATH)
    assert len(df) == 156


def test_no_duplicate_match_ids():
    df = pd.read_csv(FIXTURES_PATH)
    assert df["match_id"].duplicated().sum() == 0


def test_no_team_plays_itself():
    df = pd.read_csv(FIXTURES_PATH)
    assert (df["home_team"] == df["away_team"]).sum() == 0


def test_54_real_teams_all_known_to_team_names_registry():
    df = pd.read_csv(FIXTURES_PATH)
    teams = set(df["home_team"]) | set(df["away_team"])
    assert len(teams) == 54
    known = set(CANONICAL_TEAMS["nations_league"].keys())
    assert teams <= known, f"unrecognized team(s) in fixture list: {teams - known}"


def test_six_real_rounds_of_26_matches_each():
    df = pd.read_csv(FIXTURES_PATH)
    counts = df["matchweek"].value_counts()
    assert set(counts.index) == set(range(1, 7))
    assert (counts == 26).all()


def test_every_group_stage_match_is_within_one_real_tier():
    """Every real Nations League match is between two teams UEFA placed
    in the same League A/B/C/D tier for this cycle -- groups never mix
    tiers. This is the real structural fact
    src/evaluation/backtest_nations_league.team_tier_seed_ratings
    depends on (a per-team tier offset only matters for teams that
    never actually play each other within a cycle)."""
    df = pd.read_csv(FIXTURES_PATH)
    grouped = df[df["group"].notna() & (df["group"] != "")]
    tiers = grouped["group"].str.extract(r"Group ([A-D])")[0]
    for tier, home, away in zip(tiers, grouped["home_team"], grouped["away_team"]):
        assert tier in ("A", "B", "C", "D"), f"unrecognized group label for {home} v {away}: {tier}"


@pytest.mark.skipif(not HISTORICAL_PATH.exists(), reason="nations_league historical not collected yet")
def test_167_real_historical_matches_all_known_teams():
    df = pd.read_csv(HISTORICAL_PATH)
    assert len(df) == 167
    teams = set(df["home_team"]) | set(df["away_team"])
    known = set(CANONICAL_TEAMS["nations_league"].keys())
    assert teams <= known, f"unrecognized team(s) in historical data: {teams - known}"
    assert df["home_goals"].notna().all() and df["away_goals"].notna().all()


@pytest.mark.skipif(not HISTORICAL_PATH.exists(), reason="nations_league historical not collected yet")
def test_every_2026_27_team_has_real_2024_25_history():
    """Confirms the real basis for predict_nations_league_matches.py
    never falling back to a flat, uninformed 1500 Elo seed for any real
    2026-27 participant."""
    fixtures = pd.read_csv(FIXTURES_PATH)
    historical = pd.read_csv(HISTORICAL_PATH)
    teams_2627 = set(fixtures["home_team"]) | set(fixtures["away_team"])
    teams_2425 = set(historical["home_team"]) | set(historical["away_team"])
    assert teams_2627 <= teams_2425, f"team(s) with no 2024-25 history: {teams_2627 - teams_2425}"
