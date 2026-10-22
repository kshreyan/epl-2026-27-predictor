import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import all_league_ids, league_path, load_league_config  # noqa: E402
from src.utils.team_names import CANONICAL_TEAMS  # noqa: E402

# "swiss"-format leagues (UCL/UEL/UECL's 36-team partial-schedule league
# phase) are excluded from single_table_league_ids() and get their own,
# differently-shaped integrity checks here rather than
# test_fixture_integrity.py's round-robin assertions, which don't apply
# to a real partial schedule (each team plays only 8 or 6 of the other
# 35 teams, not all of them). Scoped specifically to format=="swiss",
# not just "non-single_table" -- NFL/NBA (format=="points") are also
# excluded from single_table_league_ids() but have a real, different
# season shape (no expected_fixture_count override, no 18-match-per-
# round structure) and get their own integrity test instead.
CONTINENTAL_CUP_LEAGUE_IDS = [lid for lid in all_league_ids() if load_league_config(lid).format == "swiss"]


def _fixtures_path_for(league_id: str) -> Path:
    return REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")


def _skip_reason(league_id: str) -> str | None:
    if not _fixtures_path_for(league_id).exists():
        return f"{league_id}: fixtures not collected yet -- run collect_fixtures.py --league {league_id}"
    return None


@pytest.mark.parametrize("league_id", CONTINENTAL_CUP_LEAGUE_IDS)
def test_real_fixture_count_matches_expected_swiss_schedule(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    cfg = load_league_config(league_id)
    df = pd.read_csv(_fixtures_path_for(league_id))
    assert cfg.expected_fixture_count is not None, f"{league_id}: swiss-format league needs an expected_fixture_count override"
    assert len(df) == cfg.expected_fixture_count
    assert df["match_id"].duplicated().sum() == 0
    assert (df["home_team"] == df["away_team"]).sum() == 0


@pytest.mark.parametrize("league_id", CONTINENTAL_CUP_LEAGUE_IDS)
def test_real_fixture_count_has_36_teams_each_playing_the_real_partial_schedule(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    cfg = load_league_config(league_id)
    df = pd.read_csv(_fixtures_path_for(league_id))

    teams = set(df["home_team"]) | set(df["away_team"])
    assert len(teams) == cfg.n_teams
    # Every real 2026-27 participant must be one this league's canonical
    # registry actually knows about -- catches a team-alias gap before
    # it ever reaches normalize_team_name() in production.
    known = set(CANONICAL_TEAMS[league_id].keys())
    assert teams <= known, f"{league_id}: unrecognized team(s) in fixture list: {teams - known}"

    games_per_team = cfg.expected_fixture_count * 2 // cfg.n_teams
    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    assert (counts == games_per_team).all(), f"{league_id}: not every team plays exactly {games_per_team} real league-phase matches"

    # No team plays the same opponent twice (unlike a domestic double
    # round-robin, a Swiss-model league phase schedules each pairing at
    # most once).
    pairs = list(zip(df["home_team"], df["away_team"])) + list(zip(df["away_team"], df["home_team"]))
    normalized_pairs = {tuple(sorted(p)) for p in pairs}
    assert len(normalized_pairs) == len(df)


@pytest.mark.parametrize("league_id", CONTINENTAL_CUP_LEAGUE_IDS)
def test_real_league_phase_rounds_have_18_matches_each(league_id):
    reason = _skip_reason(league_id)
    if reason:
        pytest.skip(reason)
    cfg = load_league_config(league_id)
    df = pd.read_csv(_fixtures_path_for(league_id))

    n_rounds = cfg.expected_fixture_count // (cfg.n_teams // 2)
    counts = df["matchweek"].value_counts()
    assert set(counts.index) == set(range(1, n_rounds + 1))
    assert (counts == cfg.n_teams // 2).all()
