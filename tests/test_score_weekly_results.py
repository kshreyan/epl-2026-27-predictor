"""Tests the weekly scoring pass in isolation, with fully synthetic
data -- no dependency on real fixture/historical files, so these run
fast (unlike the real-data slow end-to-end tests in
test_completed_match_locking.py)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.prediction_ledger import append_to_ledger  # noqa: E402
from src.evaluation.score_weekly_results import (  # noqa: E402
    build_reliability_table,
    most_surprising_results,
    score_after_matchweek,
    score_predictions,
)
from src.update_after_matchweek import WeeklyUpdatePaths  # noqa: E402


@pytest.fixture
def tmp_paths(tmp_path) -> WeeklyUpdatePaths:
    return WeeklyUpdatePaths(
        historical=tmp_path / "historical.csv", fixtures=tmp_path / "fixtures.csv",
        completed_2627=tmp_path / "completed.csv", model_config=tmp_path / "model.yaml",
        sim_config=tmp_path / "sim.yaml", predictions=tmp_path / "predictions.csv",
        expected_table=tmp_path / "expected_table.csv", position_distribution=tmp_path / "position.csv",
        weekly_dir=tmp_path / "weekly", ledger=tmp_path / "ledger.csv",
        weekly_scoring=tmp_path / "weekly_scoring.csv", reliability_running=tmp_path / "reliability_running.csv",
        season_probability_path=tmp_path / "season_probability_path.csv",
        recalibration_decisions=tmp_path / "recalibration_decisions.csv",
        active_calibrators=tmp_path / "active_calibrators.pkl",
    )


def _pred_row(match_id, matchweek, home, away, kickoff, generated_at, h, d, a, dc_h=None, dc_d=None, dc_a=None):
    return {
        "match_id": match_id, "matchweek": matchweek, "home_team": home, "away_team": away,
        "kickoff_utc": kickoff,
        "home_win_prob_model_only": h, "draw_prob_model_only": d, "away_win_prob_model_only": a,
        "dc_raw_home_win_prob": dc_h if dc_h is not None else h,
        "dc_raw_draw_prob": dc_d if dc_d is not None else d,
        "dc_raw_away_win_prob": dc_a if dc_a is not None else a,
        "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
        "market_available": False, "prediction_mode": "preseason_mode", "run_id": f"run_{match_id}",
        "model_version": "test", "generated_at": generated_at,
    }


def _write_fixtures_and_completed(tmp_paths, rows):
    """rows: list of (match_id, matchweek, home, away, kickoff, home_goals, away_goals)."""
    fixtures = pd.DataFrame([{
        "match_id": r[0], "matchweek": r[1], "home_team": r[2], "away_team": r[3], "kickoff_utc": r[4],
    } for r in rows])
    fixtures.to_csv(tmp_paths.fixtures, index=False)

    def _result(hg, ag):
        return "home_win" if hg > ag else ("away_win" if hg < ag else "draw")

    completed = pd.DataFrame([{
        "date": r[4][:10], "match_id": r[0], "home_team": r[2], "away_team": r[3],
        "home_goals": r[5], "away_goals": r[6], "result": _result(r[5], r[6]),
    } for r in rows])
    completed.to_csv(tmp_paths.completed_2627, index=False)


def test_score_predictions_computes_metrics_per_model():
    scored = pd.DataFrame([
        {"home_win_prob": 0.7, "draw_prob": 0.2, "away_win_prob": 0.1,
         "dc_raw_home_win_prob": 0.6, "dc_raw_draw_prob": 0.25, "dc_raw_away_win_prob": 0.15,
         "market_home_win_prob": None, "market_draw_prob": None, "market_away_win_prob": None,
         "market_available": False, "actual_result": "home_win"},
        {"home_win_prob": 0.3, "draw_prob": 0.3, "away_win_prob": 0.4,
         "dc_raw_home_win_prob": 0.35, "dc_raw_draw_prob": 0.3, "dc_raw_away_win_prob": 0.35,
         "market_home_win_prob": None, "market_draw_prob": None, "market_away_win_prob": None,
         "market_available": False, "actual_result": "away_win"},
    ])
    metrics = score_predictions(scored)
    production = metrics[metrics["model"] == "production"].iloc[0]
    assert production["n_matches"] == 2
    assert production["log_loss"] > 0
    market = metrics[metrics["model"] == "market"].iloc[0]
    assert market["n_matches"] == 0
    assert pd.isna(market["log_loss"])


def test_build_reliability_table_bins_by_predicted_probability():
    scored = pd.DataFrame([
        {"home_win_prob": 0.85, "draw_prob": 0.1, "away_win_prob": 0.05, "actual_result": "home_win"},
        {"home_win_prob": 0.82, "draw_prob": 0.1, "away_win_prob": 0.08, "actual_result": "away_win"},
    ])
    table = build_reliability_table(scored, model="production")
    home_bin = table[(table["outcome_class"] == "home_win") & (table["bin_lower"] == 0.8)]
    assert home_bin.iloc[0]["n_matches"] == 2
    assert home_bin.iloc[0]["empirical_frequency"] == 0.5


def test_most_surprising_results_ranks_lowest_predicted_probability_first():
    scored = pd.DataFrame([
        {"match_id": "a", "matchweek": 1, "home_team": "X", "away_team": "Y",
         "home_win_prob": 0.9, "draw_prob": 0.07, "away_win_prob": 0.03, "actual_result": "away_win"},
        {"match_id": "b", "matchweek": 1, "home_team": "P", "away_team": "Q",
         "home_win_prob": 0.5, "draw_prob": 0.3, "away_win_prob": 0.2, "actual_result": "home_win"},
    ])
    surprising = most_surprising_results(scored, n=2)
    assert surprising.iloc[0]["match_id"] == "a"  # 0.03 assigned to what happened -- the bigger shock
    assert surprising.iloc[0]["predicted_probability_of_actual_outcome"] == 0.03


def test_score_after_matchweek_uses_only_pre_kickoff_ledger_rows_and_appends(tmp_paths):
    rows = [
        ("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", 2, 0),
        ("m2", 1, "Home2", "Away2", "2026-08-22T15:00:00+00:00", 1, 1),
    ]
    _write_fixtures_and_completed(tmp_paths, rows)

    append_to_ledger([
        _pred_row("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", "2026-08-15T00:00:00+00:00", 0.6, 0.25, 0.15),
        _pred_row("m2", 1, "Home2", "Away2", "2026-08-22T15:00:00+00:00", "2026-08-15T00:00:00+00:00", 0.4, 0.3, 0.3),
        # A later, post-kickoff row for m1 must NEVER be the one scored.
        _pred_row("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", "2026-08-23T00:00:00+00:00", 0.99, 0.005, 0.005),
    ], tmp_paths.ledger)

    result = score_after_matchweek(1, tmp_paths)
    assert len(result["gameweek_scored"]) == 2
    scored_m1 = result["gameweek_scored"][result["gameweek_scored"]["match_id"] == "m1"].iloc[0]
    assert scored_m1["home_win_prob"] == 0.6  # the pre-kickoff row, not the leaked 0.99 one

    assert tmp_paths.weekly_scoring.exists()
    first_write = pd.read_csv(tmp_paths.weekly_scoring)
    assert (first_write["matchweek"] == 1).all()

    # A second matchweek's score must APPEND, not overwrite.
    rows2 = [("m3", 2, "Home3", "Away3", "2026-08-29T15:00:00+00:00", 0, 2)]
    _write_fixtures_and_completed(tmp_paths, rows + rows2)
    append_to_ledger([
        _pred_row("m3", 2, "Home3", "Away3", "2026-08-29T15:00:00+00:00", "2026-08-15T00:00:00+00:00", 0.3, 0.3, 0.4),
    ], tmp_paths.ledger)
    score_after_matchweek(2, tmp_paths)
    second_write = pd.read_csv(tmp_paths.weekly_scoring)
    assert set(second_write["matchweek"]) == {1, 2}
    assert len(second_write) > len(first_write)


def test_score_after_matchweek_raises_if_no_pre_kickoff_prediction_exists(tmp_paths):
    rows = [("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", 2, 0)]
    _write_fixtures_and_completed(tmp_paths, rows)
    # No ledger entry at all for m1 -- this must fail loudly, never
    # silently score nothing or fall back to some regenerated value.
    with pytest.raises(ValueError, match="No pre-kickoff prediction"):
        score_after_matchweek(1, tmp_paths)
