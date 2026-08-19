"""Tests the weekly-update engine's result-locking mechanism.

Uses SYNTHETIC scores for real matchweek-1 fixtures, written only to a
temporary directory via WeeklyUpdatePaths -- never to the real project
data files (data/raw/epl_2026_27_fixtures.csv etc. are never touched
by this test). This proves the locking mechanism works even though no
real 2026-27 result exists yet (today is before kickoff).
"""
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import src.utils.versioning as versioning  # noqa: E402
from src.evaluation.prediction_ledger import append_to_ledger  # noqa: E402
from src.update_after_matchweek import (  # noqa: E402
    WeeklyUpdatePaths,
    lock_completed_matches,
    load_results,
    run_update,
)

REAL_FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
REAL_HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
REAL_MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
REAL_SIM_CONFIG_PATH = REPO_ROOT / "config" / "simulation_config.yaml"

pytestmark = pytest.mark.skipif(
    not (REAL_FIXTURES_PATH.exists() and REAL_HISTORICAL_PATH.exists()),
    reason="requires the real fixture/historical data collectors to have been run first",
)


@pytest.fixture(autouse=True)
def redirect_experiment_log(tmp_path, monkeypatch):
    """run_update() calls log_experiment(), which writes to a module-level
    global path -- redirect it to tmp_path so this synthetic test run
    never appends a fake 'weekly_update' row to the real
    experiments/epl_2026_27_experiment_log.csv (see the equivalent
    fixture in test_weekly_update_versioning.py for why this matters)."""
    monkeypatch.setattr(versioning, "EXPERIMENT_LOG", tmp_path / "test_experiment_log.csv")


@pytest.fixture
def tmp_paths(tmp_path) -> WeeklyUpdatePaths:
    """A full WeeklyUpdatePaths pointed entirely at tmp_path, except
    `historical` and `model_config` which are read-only real files safe
    to reuse. `fixtures` is a COPY of the real fixture list (so
    match_ids are real and valid), never the real file itself."""
    fixtures_copy = tmp_path / "fixtures.csv"
    shutil.copy(REAL_FIXTURES_PATH, fixtures_copy)

    # Small n_simulations for test speed -- a temp copy of the real sim
    # config with the count overridden, not a hand-written config that
    # could drift from the real schema.
    with open(REAL_SIM_CONFIG_PATH) as f:
        sim_cfg = yaml.safe_load(f)
    sim_cfg["n_simulations"] = 300
    sim_config_copy = tmp_path / "simulation_config.yaml"
    with open(sim_config_copy, "w") as f:
        yaml.safe_dump(sim_cfg, f)

    return WeeklyUpdatePaths(
        historical=REAL_HISTORICAL_PATH,
        fixtures=fixtures_copy,
        completed_2627=tmp_path / "completed.csv",
        model_config=REAL_MODEL_CONFIG_PATH,
        sim_config=sim_config_copy,
        predictions=tmp_path / "predictions.csv",
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


@pytest.fixture
def synthetic_matchweek1_results(tmp_path) -> Path:
    """SYNTHETIC scores for real matchweek-1 match_ids -- clearly test
    data, written only to tmp_path, never asserted as a real result
    anywhere else in the project."""
    fixtures = pd.read_csv(REAL_FIXTURES_PATH)
    mw1 = fixtures[fixtures["matchweek"] == 1].head(3)
    results = pd.DataFrame({
        "match_id": mw1["match_id"].tolist(),
        "home_goals": [2, 0, 1],
        "away_goals": [1, 0, 1],
        "source_name": ["synthetic_test_fixture"] * 3,
        "source_timestamp": ["2026-08-22T12:00:00+00:00"] * 3,
    })
    path = tmp_path / "synthetic_results.csv"
    results.to_csv(path, index=False)
    return path


def test_load_results_requires_all_columns(tmp_path):
    bad = tmp_path / "bad_results.csv"
    pd.DataFrame({"match_id": ["x"], "home_goals": [1]}).to_csv(bad, index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        load_results(bad)


def test_lock_completed_matches_marks_status_and_writes_completed_file(tmp_paths, synthetic_matchweek1_results):
    fixtures_df = pd.read_csv(tmp_paths.fixtures)
    results = load_results(synthetic_matchweek1_results)
    locked_ids = set(results["match_id"])

    updated = lock_completed_matches(1, results, fixtures_df, tmp_paths)

    assert (updated.loc[updated["match_id"].isin(locked_ids), "status"] == "completed").all()
    not_locked = updated[~updated["match_id"].isin(locked_ids)]
    assert (not_locked["status"] != "completed").all()

    assert tmp_paths.completed_2627.exists()
    completed = pd.read_csv(tmp_paths.completed_2627)
    assert set(completed["match_id"]) == locked_ids
    assert (completed["is_real_data"] == True).all()  # noqa: E712
    assert (completed["source_name"] == "synthetic_test_fixture").all()


def test_lock_completed_matches_rejects_match_id_outside_the_matchweek(tmp_paths):
    fixtures_df = pd.read_csv(tmp_paths.fixtures)
    mw2_id = fixtures_df[fixtures_df["matchweek"] == 2].iloc[0]["match_id"]
    bad_results = pd.DataFrame({
        "match_id": [mw2_id], "home_goals": [1], "away_goals": [0],
        "source_name": ["synthetic_test_fixture"], "source_timestamp": ["2026-08-22T12:00:00+00:00"],
    })
    with pytest.raises(ValueError, match="not in matchweek"):
        lock_completed_matches(1, bad_results, fixtures_df, tmp_paths)


def test_lock_completed_matches_upserts_a_correction(tmp_paths, synthetic_matchweek1_results):
    fixtures_df = pd.read_csv(tmp_paths.fixtures)
    results = load_results(synthetic_matchweek1_results)
    lock_completed_matches(1, results, fixtures_df, tmp_paths)

    corrected = results.copy()
    corrected.loc[0, "home_goals"] = 9  # a deliberately different score, simulating a real correction
    lock_completed_matches(1, corrected, pd.read_csv(tmp_paths.fixtures), tmp_paths)

    completed = pd.read_csv(tmp_paths.completed_2627)
    assert len(completed) == len(results)  # upsert, not duplicate
    assert int(completed.loc[completed["match_id"] == corrected.iloc[0]["match_id"], "home_goals"].iloc[0]) == 9


def _seed_ledger_pre_kickoff(tmp_paths, results_path):
    """Writes a synthetic pre-kickoff ledger row for each match_id in
    `results_path`, mimicking what the real preseason predict_all_matches.py
    run would already have produced before this matchweek's own kickoff --
    scoring now requires this to exist (see score_after_matchweek), the
    same as it would in real production."""
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


@pytest.mark.slow
def test_run_update_end_to_end_locks_results_and_predicts_remaining(tmp_paths, synthetic_matchweek1_results):
    _seed_ledger_pre_kickoff(tmp_paths, synthetic_matchweek1_results)
    result = run_update(matchweek=1, results_path=synthetic_matchweek1_results, paths=tmp_paths)

    locked_ids = set(pd.read_csv(synthetic_matchweek1_results)["match_id"])
    fixtures_df = result["fixtures_df"]
    assert (fixtures_df.loc[fixtures_df["match_id"].isin(locked_ids), "status"] == "completed").all()

    final_predictions = result["final_predictions"]
    completed_rows = final_predictions[final_predictions["match_id"].isin(locked_ids)]
    assert completed_rows["actual_home_goals"].notna().all()
    assert (completed_rows["status"] == "completed").all()

    # "" not NaN in the in-memory frame (blank fields only become NaN after
    # a CSV round-trip); re-read the actual written file for that check.
    remaining_rows = final_predictions[~final_predictions["match_id"].isin(locked_ids)]
    assert (remaining_rows["actual_home_goals"] == "").all()
    assert (remaining_rows["prediction_mode"] == "early_week_mode").all()

    on_disk = pd.read_csv(tmp_paths.predictions)
    on_disk_remaining = on_disk[~on_disk["match_id"].isin(locked_ids)]
    assert on_disk_remaining["actual_home_goals"].isna().all()

    new_table = result["new_expected_table"]
    assert len(new_table) == 20
    assert abs(new_table["expected_wins"].add(new_table["expected_draws"]).add(new_table["expected_losses"]).sub(38).max()) < 0.05

    assert (tmp_paths.weekly_dir / "epl_matchweek_01_predictions.csv").exists()
    assert (tmp_paths.weekly_dir / "epl_matchweek_01_expected_table.csv").exists()
    assert (tmp_paths.weekly_dir / "epl_matchweek_01_update_report.md").exists()
