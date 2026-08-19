"""Tests the weekly auto-update orchestrator: which matchweeks it
decides have "concluded" (fast, no I/O), and a full run against
synthetic data with the live-results network call replaced by a fixed
in-memory DataFrame (slow, since it exercises the real refit/predict/
simulate/score/recalibration-gate path through run_update, exactly
like test_completed_match_locking.py's end-to-end test)."""
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import src.utils.versioning as versioning  # noqa: E402
import src.weekly_auto_update as weekly_auto_update  # noqa: E402
from src.evaluation.prediction_ledger import append_to_ledger  # noqa: E402
from src.update_after_matchweek import WeeklyUpdatePaths  # noqa: E402
from src.weekly_auto_update import determine_newly_complete_matchweeks, run_auto_update  # noqa: E402

REAL_FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
REAL_HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
REAL_MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
REAL_SIM_CONFIG_PATH = REPO_ROOT / "config" / "simulation_config.yaml"


def _fixtures(rows):
    return pd.DataFrame([{"match_id": r[0], "matchweek": r[1]} for r in rows])


def test_no_op_when_no_matchweek_is_fully_complete():
    fixtures = _fixtures([("m1", 1), ("m2", 1), ("m3", 2)])
    live = pd.DataFrame({"match_id": ["m1"]})  # only 1 of matchweek 1's 2 matches done
    completed = pd.DataFrame(columns=["match_id"])
    assert determine_newly_complete_matchweeks(fixtures, live, completed) == []


def test_detects_a_fully_complete_unlocked_matchweek():
    fixtures = _fixtures([("m1", 1), ("m2", 1), ("m3", 2)])
    live = pd.DataFrame({"match_id": ["m1", "m2"]})
    completed = pd.DataFrame(columns=["match_id"])
    assert determine_newly_complete_matchweeks(fixtures, live, completed) == [1]


def test_skips_a_matchweek_thats_already_locked():
    fixtures = _fixtures([("m1", 1), ("m2", 1)])
    live = pd.DataFrame({"match_id": ["m1", "m2"]})
    completed = pd.DataFrame({"match_id": ["m1", "m2"]})
    assert determine_newly_complete_matchweeks(fixtures, live, completed) == []


def test_returns_multiple_matchweeks_in_chronological_order():
    fixtures = _fixtures([("m1", 1), ("m2", 2), ("m3", 3)])
    live = pd.DataFrame({"match_id": ["m1", "m2", "m3"]})
    completed = pd.DataFrame(columns=["match_id"])
    assert determine_newly_complete_matchweeks(fixtures, live, completed) == [1, 2, 3]


@pytest.fixture(autouse=True)
def redirect_experiment_log(tmp_path, monkeypatch):
    monkeypatch.setattr(versioning, "EXPERIMENT_LOG", tmp_path / "test_experiment_log.csv")


@pytest.fixture
def tmp_paths(tmp_path) -> WeeklyUpdatePaths:
    fixtures_copy = tmp_path / "fixtures.csv"
    shutil.copy(REAL_FIXTURES_PATH, fixtures_copy)
    with open(REAL_SIM_CONFIG_PATH) as f:
        sim_cfg = yaml.safe_load(f)
    sim_cfg["n_simulations"] = 300
    sim_config_copy = tmp_path / "simulation_config.yaml"
    with open(sim_config_copy, "w") as f:
        yaml.safe_dump(sim_cfg, f)
    return WeeklyUpdatePaths(
        historical=REAL_HISTORICAL_PATH, fixtures=fixtures_copy,
        completed_2627=tmp_path / "completed.csv", model_config=REAL_MODEL_CONFIG_PATH,
        sim_config=sim_config_copy, predictions=tmp_path / "predictions.csv",
        expected_table=tmp_path / "expected_table.csv", position_distribution=tmp_path / "position.csv",
        weekly_dir=tmp_path / "weekly", ledger=tmp_path / "ledger.csv",
        weekly_scoring=tmp_path / "weekly_scoring.csv", reliability_running=tmp_path / "reliability_running.csv",
        reliability_horizon=tmp_path / "reliability_horizon.csv",
        season_probability_path=tmp_path / "season_probability_path.csv",
        recalibration_decisions=tmp_path / "recalibration_decisions.csv",
        active_calibrators=tmp_path / "active_calibrators.pkl",
        match_odds=tmp_path / "match_odds.csv", real_odds=tmp_path / "real_odds.csv",
    )


@pytest.mark.slow
def test_run_auto_update_locks_a_concluded_matchweek_end_to_end(tmp_paths, tmp_path, monkeypatch):
    fixtures = pd.read_csv(REAL_FIXTURES_PATH)
    mw1 = fixtures[fixtures["matchweek"] == 1]

    # Seed a pre-kickoff ledger entry for every matchweek-1 fixture, same
    # as a real preseason run would already have produced.
    pred_rows = []
    for _, fx in mw1.iterrows():
        kickoff = pd.Timestamp(fx["kickoff_utc"])
        pred_rows.append({
            "match_id": fx["match_id"], "matchweek": fx["matchweek"],
            "home_team": fx["home_team"], "away_team": fx["away_team"], "kickoff_utc": fx["kickoff_utc"],
            "home_win_prob_model_only": 0.4, "draw_prob_model_only": 0.3, "away_win_prob_model_only": 0.3,
            "dc_raw_home_win_prob": 0.4, "dc_raw_draw_prob": 0.3, "dc_raw_away_win_prob": 0.3,
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "market_available": False, "prediction_mode": "preseason_mode", "run_id": "seed_run",
            "model_version": "test", "generated_at": (kickoff - pd.Timedelta(days=7)).isoformat(),
        })
    append_to_ledger(pred_rows, tmp_paths.ledger)

    # A fake "live results" feed: every matchweek-1 match finished 2-1.
    fake_live_results = pd.DataFrame({
        "match_id": mw1["match_id"].tolist(),
        "home_goals": [2] * len(mw1), "away_goals": [1] * len(mw1),
        "source_name": ["football-data.co.uk"] * len(mw1),
        "source_timestamp": ["2026-08-25T00:00:00+00:00"] * len(mw1),
    })
    monkeypatch.setattr(weekly_auto_update, "fetch_all_live_results", lambda fixtures_path: fake_live_results)

    processed = run_auto_update(paths=tmp_paths)

    assert len(processed) == 1
    assert processed[0]["matchweek"] == 1
    assert processed[0]["n_results"] == len(mw1)

    completed = pd.read_csv(tmp_paths.completed_2627)
    assert set(completed["match_id"]) == set(mw1["match_id"])

    # A second call with the SAME live results must be a real no-op --
    # matchweek 1 is already locked.
    processed_again = run_auto_update(paths=tmp_paths)
    assert processed_again == []
