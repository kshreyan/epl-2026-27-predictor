import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import all_league_ids, league_path, load_league_config  # noqa: E402
from src.utils.team_names import CANONICAL_TEAMS  # noqa: E402

# "points"-format leagues (NFL/NBA -- real American team sports, real
# points not goals) are excluded from single_table_league_ids() (no
# goal-difference-tiebreak table concept applies) and get their own
# integrity checks here, separate from the Swiss-format continental
# cups (test_continental_cup_fixture_integrity.py): no
# expected_fixture_count override exists for these (the real season
# schedule is collected progressively from ESPN, not published in
# full in advance the way a soccer fixture list is -- see
# collect_espn_schedule.py's own docstring on this real limitation).
TEAM_SPORT_LEAGUE_IDS = [lid for lid in all_league_ids() if load_league_config(lid).format == "points"]


def _fixtures_path_for(league_id: str) -> Path:
    return REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")


def _skip_reason(league_id: str) -> str | None:
    if not _fixtures_path_for(league_id).exists():
        return f"{league_id}: fixtures not collected yet -- run collect_espn_schedule.py --league {league_id}"
    return None


@pytest.mark.parametrize("league_id", TEAM_SPORT_LEAGUE_IDS)
def test_real_fixtures_have_no_duplicates_or_self_matches(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    df = pd.read_csv(_fixtures_path_for(league_id))
    assert len(df) > 0
    assert df["match_id"].duplicated().sum() == 0
    assert (df["home_team"] == df["away_team"]).sum() == 0


@pytest.mark.parametrize("league_id", TEAM_SPORT_LEAGUE_IDS)
def test_real_fixtures_teams_are_all_known_and_within_expected_count(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    cfg = load_league_config(league_id)
    df = pd.read_csv(_fixtures_path_for(league_id))

    teams = set(df["home_team"]) | set(df["away_team"])
    assert len(teams) <= cfg.n_teams, f"{league_id}: found more teams than the real league has ({len(teams)} > {cfg.n_teams})"
    known = set(CANONICAL_TEAMS[league_id].keys())
    assert teams <= known, f"{league_id}: unrecognized team(s) in fixture list: {teams - known}"


@pytest.mark.parametrize("league_id", TEAM_SPORT_LEAGUE_IDS)
def test_real_fixtures_status_and_result_consistency(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    df = pd.read_csv(_fixtures_path_for(league_id))
    # collect_espn_schedule.py always writes status="scheduled" (real
    # results live in a separate {league}_2026_27_real_results.csv
    # ledger, same convention every other league in this project uses).
    assert (df["status"] == "scheduled").all()
