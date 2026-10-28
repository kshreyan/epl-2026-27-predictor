"""Tests the CLV module: real snapshot history must accumulate
append-only, and realized CLV is only computed for a match with at
least two real pre-kickoff snapshots -- never estimated from one."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.closing_line_value import (  # noqa: E402
    _snapshot_path,
    append_odds_snapshot,
    compute_clv,
    compute_realized_clv,
)

TEST_LEAGUE = "test_clv_league"


@pytest.fixture(autouse=True)
def _clean_test_snapshot_file():
    path = _snapshot_path(TEST_LEAGUE)
    if path.exists():
        path.unlink()
    yield
    if path.exists():
        path.unlink()


def test_compute_clv_positive_means_closing_favored_the_backed_side():
    assert compute_clv(opening_prob=0.55, closing_prob=0.60) == pytest.approx(0.05)


def test_compute_clv_negative_means_closing_moved_against():
    assert compute_clv(opening_prob=0.55, closing_prob=0.50) == pytest.approx(-0.05)


def test_realized_clv_is_empty_with_no_snapshot_file():
    result = compute_realized_clv(TEST_LEAGUE)
    assert result.empty


def test_realized_clv_excludes_a_match_with_only_one_pre_kickoff_snapshot():
    append_odds_snapshot(TEST_LEAGUE, [{
        "match_id": "GAME_1", "snapshot_timestamp": "2026-10-20T12:00:00+00:00",
        "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.55, "away_fair_prob": 0.45,
        "devig_method": "power", "run_id": "r1",
    }])
    result = compute_realized_clv(TEST_LEAGUE)
    assert result.empty


def test_realized_clv_computes_from_earliest_and_latest_pre_kickoff_snapshots():
    append_odds_snapshot(TEST_LEAGUE, [
        {"match_id": "GAME_1", "snapshot_timestamp": "2026-10-20T12:00:00+00:00",
         "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.50, "away_fair_prob": 0.50,
         "devig_method": "power", "run_id": "r1"},
        {"match_id": "GAME_1", "snapshot_timestamp": "2026-10-25T12:00:00+00:00",
         "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.55, "away_fair_prob": 0.45,
         "devig_method": "power", "run_id": "r2"},
        # A snapshot AFTER kickoff must never be used as a "closing" proxy.
        {"match_id": "GAME_1", "snapshot_timestamp": "2026-11-02T12:00:00+00:00",
         "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.90, "away_fair_prob": 0.10,
         "devig_method": "power", "run_id": "r3"},
    ])
    result = compute_realized_clv(TEST_LEAGUE)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["n_snapshots"] == 2
    assert row["opening_home_prob"] == pytest.approx(0.50)
    assert row["closing_home_prob"] == pytest.approx(0.55)
    assert row["clv_home"] == pytest.approx(0.05)


def test_append_odds_snapshot_is_append_only():
    append_odds_snapshot(TEST_LEAGUE, [{
        "match_id": "GAME_1", "snapshot_timestamp": "2026-10-20T12:00:00+00:00",
        "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.5, "away_fair_prob": 0.5,
        "devig_method": "power", "run_id": "r1",
    }])
    append_odds_snapshot(TEST_LEAGUE, [{
        "match_id": "GAME_2", "snapshot_timestamp": "2026-10-20T12:00:00+00:00",
        "kickoff_utc": "2026-11-01T18:00:00+00:00", "home_fair_prob": 0.6, "away_fair_prob": 0.4,
        "devig_method": "power", "run_id": "r2",
    }])
    import pandas as pd
    df = pd.read_csv(_snapshot_path(TEST_LEAGUE))
    assert len(df) == 2
    assert set(df["match_id"]) == {"GAME_1", "GAME_2"}
