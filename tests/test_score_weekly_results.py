"""Tests the weekly scoring pass in isolation, with fully synthetic
data -- no dependency on real fixture/historical files, so these run
fast (unlike the real-data slow end-to-end tests in
test_completed_match_locking.py). Covers the horizon-aware, two-track
(preseason vs operational) scoring added after a review flagged that
pooling predictions made at very different lead times before kickoff
would hide real calibration differences."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.prediction_ledger import append_to_ledger, read_ledger  # noqa: E402
from src.evaluation.score_weekly_results import (  # noqa: E402
    build_horizon_reliability_table,
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
        reliability_horizon=tmp_path / "reliability_horizon.csv",
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


def _synthetic_preseason_loader(rows):
    """A fake `preseason_ledger_loader` returning a fixed, distinct set
    of predictions -- so tests can prove the preseason track is scored
    independently of whatever the operational ledger holds, never
    pooled with it."""
    def _loader():
        pred_rows = [_pred_row(*r) for r in rows]
        from src.evaluation.prediction_ledger import prediction_rows_to_ledger_rows
        ledger_rows = prediction_rows_to_ledger_rows(pred_rows)
        df = pd.DataFrame(ledger_rows)
        df["kickoff_utc"] = pd.to_datetime(df["kickoff_utc"], utc=True)
        df["generated_at"] = pd.to_datetime(df["generated_at"], utc=True)
        return df
    return _loader


def test_score_predictions_tags_track_and_computes_metrics_per_model():
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
    metrics = score_predictions(scored, track="operational")
    assert (metrics["track"] == "operational").all()
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


def test_build_horizon_reliability_table_buckets_by_days_before_kickoff(tmp_paths):
    kickoff = "2026-08-22T15:00:00+00:00"
    rows = [("m1", 1, "H", "A", kickoff, 2, 0)]
    _write_fixtures_and_completed(tmp_paths, rows)
    # Two predictions for the SAME match at very different lead times:
    # one made 60 days out (bucket 31+), one made 1 day out (bucket 0-2).
    append_to_ledger([
        _pred_row("m1", 1, "H", "A", kickoff, "2026-06-23T00:00:00+00:00", 0.5, 0.3, 0.2),
        _pred_row("m1", 1, "H", "A", kickoff, "2026-08-21T00:00:00+00:00", 0.9, 0.05, 0.05),
    ], tmp_paths.ledger)
    ledger = read_ledger(tmp_paths.ledger)
    completed = pd.read_csv(tmp_paths.completed_2627, parse_dates=["date"])

    table = build_horizon_reliability_table(ledger, completed, model="production")
    assert set(table["horizon_bucket"]) == {"0-2", "3-7", "8-30", "31+"}
    far_bucket = table[(table["horizon_bucket"] == "31+") & (table["outcome_class"] == "home_win") & (table["bin_lower"] == 0.5)]
    near_bucket = table[(table["horizon_bucket"] == "0-2") & (table["outcome_class"] == "home_win") & (table["bin_lower"] == 0.9)]
    assert far_bucket.iloc[0]["n_matches"] == 1
    assert near_bucket.iloc[0]["n_matches"] == 1
    # The two observations must land in DIFFERENT buckets, not be merged.
    other_buckets = table[table["horizon_bucket"].isin(["3-7", "8-30"])]
    assert other_buckets["n_matches"].sum() == 0


def test_most_surprising_results_ranks_lowest_predicted_probability_first():
    scored = pd.DataFrame([
        {"match_id": "a", "matchweek": 1, "home_team": "X", "away_team": "Y",
         "home_win_prob": 0.9, "draw_prob": 0.07, "away_win_prob": 0.03, "actual_result": "away_win"},
        {"match_id": "b", "matchweek": 1, "home_team": "P", "away_team": "Q",
         "home_win_prob": 0.5, "draw_prob": 0.3, "away_win_prob": 0.2, "actual_result": "home_win"},
    ])
    surprising = most_surprising_results(scored, n=2)
    assert surprising.iloc[0]["match_id"] == "a"
    assert surprising.iloc[0]["predicted_probability_of_actual_outcome"] == 0.03


def test_score_after_matchweek_scores_preseason_and_operational_separately(tmp_paths):
    kickoff = "2026-08-22T15:00:00+00:00"
    rows = [("m1", 1, "H1", "A1", kickoff, 2, 0), ("m2", 1, "H2", "A2", kickoff, 1, 1)]
    _write_fixtures_and_completed(tmp_paths, rows)

    # Operational ledger: the model's current best guess.
    append_to_ledger([
        _pred_row("m1", 1, "H1", "A1", kickoff, "2026-08-15T00:00:00+00:00", 0.6, 0.25, 0.15),
        _pred_row("m2", 1, "H2", "A2", kickoff, "2026-08-15T00:00:00+00:00", 0.4, 0.3, 0.3),
    ], tmp_paths.ledger)

    # Preseason track: DELIBERATELY different probabilities, so pooling
    # would be detectable.
    preseason_rows = [
        ("m1", 1, "H1", "A1", kickoff, "2026-06-01T00:00:00+00:00", 0.2, 0.3, 0.5),
        ("m2", 1, "H2", "A2", kickoff, "2026-06-01T00:00:00+00:00", 0.2, 0.3, 0.5),
    ]
    loader = _synthetic_preseason_loader(preseason_rows)

    result = score_after_matchweek(1, tmp_paths, preseason_ledger_loader=loader)

    weekly = result["weekly_scoring"]
    op_production = weekly[(weekly["track"] == "operational") & (weekly["model"] == "production") & (weekly["scope"] == "cumulative")].iloc[0]
    pre_production = weekly[(weekly["track"] == "preseason") & (weekly["model"] == "production") & (weekly["scope"] == "cumulative")].iloc[0]
    assert op_production["log_loss"] != pre_production["log_loss"]  # never pooled into one number

    # Preseason track has no dc_raw baseline available (that field
    # didn't exist yet when the real v2 tag was made) -- the synthetic
    # loader mirrors that honestly via prediction_rows_to_ledger_rows'
    # defaults, so dc_raw here happens to equal the production probs;
    # what matters is n_matches is still counted correctly per track.
    pre_dc_raw = weekly[(weekly["track"] == "preseason") & (weekly["model"] == "dc_raw") & (weekly["scope"] == "cumulative")].iloc[0]
    assert pre_dc_raw["n_matches"] == 2

    assert set(result["reliability"]["track"]) == {"operational", "preseason"}


def test_score_after_matchweek_raises_if_operational_pre_kickoff_prediction_missing(tmp_paths):
    rows = [("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", 2, 0)]
    _write_fixtures_and_completed(tmp_paths, rows)
    loader = _synthetic_preseason_loader([("m1", 1, "Home1", "Away1", "2026-08-22T15:00:00+00:00", "2026-06-01T00:00:00+00:00", 0.4, 0.3, 0.3)])
    # No operational ledger entry at all for m1 -- must fail loudly.
    with pytest.raises(ValueError, match="No pre-kickoff prediction"):
        score_after_matchweek(1, tmp_paths, preseason_ledger_loader=loader)
