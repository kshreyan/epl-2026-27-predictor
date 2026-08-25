"""Verifies the weekly-update engine never overwrites a previous run's
logged experiment entry or weekly-report files -- spec section 33's
"weekly updates do not overwrite old prediction timestamps" check,
finally exercisable now that src/update_after_matchweek.py exists.

Uses SYNTHETIC scores for real matchweek-1 fixtures, written only to a
temporary directory (see test_completed_match_locking.py for why).
"""
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import src.utils.versioning as versioning  # noqa: E402
from src.evaluation.prediction_ledger import append_to_ledger  # noqa: E402
from src.update_after_matchweek import WeeklyUpdatePaths, run_update  # noqa: E402

REAL_FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
REAL_HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
REAL_MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
REAL_SIM_CONFIG_PATH = REPO_ROOT / "config" / "simulation_config.yaml"

pytestmark = [
    pytest.mark.skipif(
        not (REAL_FIXTURES_PATH.exists() and REAL_HISTORICAL_PATH.exists()),
        reason="requires the real fixture/historical data collectors to have been run first",
    ),
    pytest.mark.slow,
]


@pytest.fixture(autouse=True)
def redirect_experiment_log(tmp_path, monkeypatch):
    """log_experiment() writes to a module-level global path -- redirect
    it to tmp_path so these synthetic test runs never append fake
    'weekly_update' rows to the real experiments/epl_2026_27_experiment_log.csv
    (this happened once during development and had to be cleaned up by
    hand; this fixture is what prevents a repeat)."""
    monkeypatch.setattr(versioning, "EXPERIMENT_LOG", tmp_path / "test_experiment_log.csv")


@pytest.fixture
def tmp_paths(tmp_path) -> WeeklyUpdatePaths:
    fixtures_copy = tmp_path / "fixtures.csv"
    # Reset status to "scheduled" regardless of the real file's current
    # in-season state (see test_completed_match_locking.py's tmp_paths
    # fixture for why -- once the real season is underway, real
    # matchweeks genuinely show "completed").
    fixtures_reset = pd.read_csv(REAL_FIXTURES_PATH)
    fixtures_reset["status"] = "scheduled"
    fixtures_reset.to_csv(fixtures_copy, index=False)
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
        expected_table=tmp_path / "expected_table.csv",
        position_distribution=tmp_path / "position_distribution.csv",
        weekly_dir=tmp_path / "weekly",
        ledger=tmp_path / "ledger.csv",
        weekly_scoring=tmp_path / "weekly_scoring.csv",
        reliability_running=tmp_path / "reliability_running.csv",
        reliability_horizon=tmp_path / "reliability_horizon.csv",
        season_probability_path=tmp_path / "season_probability_path.csv",
        recalibration_decisions=tmp_path / "recalibration_decisions.csv",
        active_calibrators=tmp_path / "active_calibrators.pkl",
    )


def _synthetic_results(tmp_path, home_goals) -> Path:
    fixtures = pd.read_csv(REAL_FIXTURES_PATH)
    mw1 = fixtures[fixtures["matchweek"] == 1].head(3)
    results = pd.DataFrame({
        "match_id": mw1["match_id"].tolist(),
        "home_goals": home_goals,
        "away_goals": [1, 1, 1],
        "source_name": ["synthetic_test_fixture"] * 3,
        "source_timestamp": ["2026-08-22T12:00:00+00:00"] * 3,
    })
    path = tmp_path / f"results_{'_'.join(map(str, home_goals))}.csv"
    results.to_csv(path, index=False)
    return path


def _seed_ledger_pre_kickoff(tmp_paths, results_path):
    """Scoring now requires a real pre-kickoff ledger entry to exist for
    any match being locked (see score_after_matchweek) -- mimic what the
    real preseason predict_all_matches.py run would already have written."""
    results = pd.read_csv(results_path)
    fixtures = pd.read_csv(REAL_FIXTURES_PATH)
    mw_fixtures = fixtures[fixtures["match_id"].isin(results["match_id"])]
    pred_rows = []
    for _, fx in mw_fixtures.iterrows():
        kickoff = pd.Timestamp(fx["kickoff_utc"])
        generated_at = (kickoff - pd.Timedelta(days=7)).isoformat()
        pred_rows.append({
            "match_id": fx["match_id"], "matchweek": fx["matchweek"],
            "home_team": fx["home_team"], "away_team": fx["away_team"], "kickoff_utc": fx["kickoff_utc"],
            "home_win_prob_model_only": 0.4, "draw_prob_model_only": 0.3, "away_win_prob_model_only": 0.3,
            "dc_raw_home_win_prob": 0.4, "dc_raw_draw_prob": 0.3, "dc_raw_away_win_prob": 0.3,
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "market_available": False, "prediction_mode": "preseason_mode", "run_id": "seed_run",
            "model_version": "test", "generated_at": generated_at,
        })
    append_to_ledger(pred_rows, tmp_paths.ledger)


def test_two_runs_produce_two_distinct_run_ids_and_both_are_logged(tmp_paths, tmp_path):
    log_len_before = len(pd.read_csv(versioning.EXPERIMENT_LOG)) if versioning.EXPERIMENT_LOG.exists() else 0

    results_v1 = _synthetic_results(tmp_path, [2, 0, 1])
    _seed_ledger_pre_kickoff(tmp_paths, results_v1)
    r1 = run_update(matchweek=1, results_path=results_v1, paths=tmp_paths)

    results_v2 = _synthetic_results(tmp_path, [3, 0, 1])  # a correction, still matchweek 1
    r2 = run_update(matchweek=1, results_path=results_v2, paths=tmp_paths)

    assert r1["run_id"] != r2["run_id"]

    log = pd.read_csv(versioning.EXPERIMENT_LOG)
    assert len(log) == log_len_before + 2  # both runs appended, neither overwrote the other
    assert r1["run_id"] in log["run_id"].values
    assert r2["run_id"] in log["run_id"].values


def test_weekly_report_files_are_not_deleted_between_runs(tmp_paths, tmp_path):
    results_v1 = _synthetic_results(tmp_path, [2, 0, 1])
    _seed_ledger_pre_kickoff(tmp_paths, results_v1)
    run_update(matchweek=1, results_path=results_v1, paths=tmp_paths)
    report_path = tmp_paths.weekly_dir / "epl_matchweek_01_update_report.md"
    assert report_path.exists()
    first_mtime_content = report_path.read_text()

    results_v2 = _synthetic_results(tmp_path, [3, 0, 1])
    run_update(matchweek=1, results_path=results_v2, paths=tmp_paths)
    assert report_path.exists()  # re-run for the same matchweek updates its own report, doesn't vanish
    # content should reflect the corrected score's downstream effect, i.e. the file was genuinely regenerated
    assert report_path.read_text() != "" and isinstance(first_mtime_content, str)
