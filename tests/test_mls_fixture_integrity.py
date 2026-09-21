"""Integrity checks for the real MLS fixture/historical data -- a
`single_table` league (see src/leagues.py) that is NOT a full round-
robin, so it does not fit test_fixture_integrity.py's
n_teams*(n_teams-1) assertion."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.team_names import CANONICAL_TEAMS  # noqa: E402

FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_fixtures.csv"
COMPLETED_PATH = REPO_ROOT / "data" / "raw" / "mls_2026_27_completed_matches.csv"
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "mls_historical_matches.csv"

pytestmark = pytest.mark.skipif(
    not FIXTURES_PATH.exists(),
    reason="mls fixtures not collected yet -- run collect_mls_fixtures.py",
)


def test_510_real_fixtures_present():
    df = pd.read_csv(FIXTURES_PATH)
    assert len(df) == 510


def test_no_duplicate_match_ids():
    df = pd.read_csv(FIXTURES_PATH)
    assert df["match_id"].duplicated().sum() == 0


def test_no_team_plays_itself():
    df = pd.read_csv(FIXTURES_PATH)
    assert (df["home_team"] == df["away_team"]).sum() == 0


def test_30_real_teams_each_playing_34_matches_all_known_to_registry():
    df = pd.read_csv(FIXTURES_PATH)
    teams = set(df["home_team"]) | set(df["away_team"])
    assert len(teams) == 30
    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    assert (counts == 34).all()
    known = set(CANONICAL_TEAMS["mls"].keys())
    assert teams <= known, f"unrecognized team(s) in fixture list: {teams - known}"


def test_status_matches_whether_a_real_score_exists():
    """collect_mls_fixtures.py sets status from real score presence at
    onboarding -- a completed row must have come from a real result,
    and status/completed_matches.csv must agree on which matches those
    are (no match marked completed in one file and not the other)."""
    df = pd.read_csv(FIXTURES_PATH)
    assert set(df["status"]) <= {"completed", "scheduled"}
    if not COMPLETED_PATH.exists():
        return
    completed = pd.read_csv(COMPLETED_PATH)
    fixtures_completed_ids = set(df[df["status"] == "completed"]["match_id"])
    assert fixtures_completed_ids == set(completed["match_id"]), "fixtures.csv/completed_matches.csv disagree on which matches are locked"
    assert completed["home_goals"].notna().all() and completed["away_goals"].notna().all()


@pytest.mark.skipif(not HISTORICAL_PATH.exists(), reason="mls historical not collected yet")
def test_1496_real_historical_matches_across_three_seasons():
    df = pd.read_csv(HISTORICAL_PATH, dtype={"season": str})
    assert len(df) == 1496
    assert set(df["season"]) == {"2023", "2024", "2025"}
    assert df["home_goals"].notna().all() and df["away_goals"].notna().all()
    known = set(CANONICAL_TEAMS["mls"].keys())
    teams = set(df["home_team"]) | set(df["away_team"])
    assert teams <= known, f"unrecognized team(s) in historical data: {teams - known}"


@pytest.mark.skipif(not HISTORICAL_PATH.exists(), reason="mls historical not collected yet")
def test_every_2026_team_has_real_prior_history():
    """Confirms the real basis for the Dixon-Coles/Elo fit never falling
    back to a flat, uninformed rating for any real 2026 participant --
    San Diego FC (real 2025 expansion club) is the one team without a
    FULL three-season history, but it does have real 2025 data."""
    fixtures = pd.read_csv(FIXTURES_PATH)
    historical = pd.read_csv(HISTORICAL_PATH, dtype={"season": str})
    teams_2026 = set(fixtures["home_team"]) | set(fixtures["away_team"])
    teams_hist = set(historical["home_team"]) | set(historical["away_team"])
    assert teams_2026 <= teams_hist, f"team(s) with no historical data: {teams_2026 - teams_hist}"
