"""Tests the tightened gated challenger recalibration process with
fully synthetic data. Confirms: (1) a real no-op below the 150-match
threshold and off the evaluation cadence; (2) every attempt is logged,
promoted or not; (3) a challenger with genuine, exploitable real-data
signal gets promoted via a paired-bootstrap 95% CI on rolling-origin
evaluations (not a single recent holdout); (4) below
ISOTONIC_MIN_REAL_MATCHES the challenger uses temperature scaling, not
isotonic."""
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.prediction_ledger import append_to_ledger  # noqa: E402
from src.evaluation.recalibration_gate import (  # noqa: E402
    EVALUATION_CADENCE_MATCHWEEKS,
    ISOTONIC_MIN_REAL_MATCHES,
    MIN_MATCHES_TO_ATTEMPT,
    attempt_recalibration,
    fit_challenger,
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


def _write_synthetic_backtest(path, n=600, home_win_true_rate=0.5):
    """A static historical backtest where the raw DC probability of
    0.5/0.3/0.2 is roughly CORRECT -- the incumbent calibrator learns
    close to identity from this."""
    rng = np.random.default_rng(0)
    draw_rate = min(0.3, (1 - home_win_true_rate) / 2)
    away_rate = 1 - home_win_true_rate - draw_rate
    results = rng.choice(["home_win", "draw", "away_win"], size=n, p=[home_win_true_rate, draw_rate, away_rate])
    df = pd.DataFrame({"dc_home_win": 0.5, "dc_draw": 0.3, "dc_away_win": 0.2, "actual_result": results})
    df.to_csv(path, index=False)


def _seed_real_matches(paths, n, home_win_true_rate, seed=1):
    """n real, completed 2026-27 matches, each with a provably
    pre-kickoff ledger prediction of dc_home_win=0.5 (the OLD, static
    backtest's belief) but actual results generated at
    `home_win_true_rate`, which can differ from the static backtest's
    0.5 to give a challenger genuine, exploitable real-data signal."""
    rng = np.random.default_rng(seed)
    draw_rate = min(0.3, (1 - home_win_true_rate) / 2)
    away_rate = 1 - home_win_true_rate - draw_rate
    results = rng.choice(["home_win", "draw", "away_win"], size=n, p=[home_win_true_rate, draw_rate, away_rate])
    fixtures_rows, completed_rows, ledger_rows = [], [], []
    for i in range(n):
        match_id = f"real_{i}"
        kickoff = pd.Timestamp("2026-08-22T15:00:00+00:00") + pd.Timedelta(days=i)
        generated_at = kickoff - pd.Timedelta(days=3)
        matchweek = 1 + i // 10
        fixtures_rows.append({"match_id": match_id, "matchweek": matchweek, "home_team": "H", "away_team": "A", "kickoff_utc": kickoff.isoformat()})
        hg, ag = {"home_win": (2, 0), "draw": (1, 1), "away_win": (0, 2)}[results[i]]
        completed_rows.append({"date": kickoff.date().isoformat(), "match_id": match_id, "home_team": "H", "away_team": "A", "home_goals": hg, "away_goals": ag, "result": results[i]})
        ledger_rows.append({
            "match_id": match_id, "matchweek": matchweek, "home_team": "H", "away_team": "A", "kickoff_utc": kickoff.isoformat(),
            "home_win_prob_model_only": 0.5, "draw_prob_model_only": 0.3, "away_win_prob_model_only": 0.2,
            "dc_raw_home_win_prob": 0.5, "dc_raw_draw_prob": 0.3, "dc_raw_away_win_prob": 0.2,
            "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
            "market_available": False, "prediction_mode": "preseason_mode", "run_id": f"run_{i}",
            "model_version": "test", "generated_at": generated_at.isoformat(),
        })
    pd.DataFrame(fixtures_rows).to_csv(paths.fixtures, index=False)
    pd.DataFrame(completed_rows).to_csv(paths.completed_2627, index=False)
    append_to_ledger(ledger_rows, paths.ledger)
    return int(np.ceil(n / 10))  # last matchweek touched


def test_below_threshold_is_a_real_noop(tmp_paths, tmp_path):
    backtest_path = tmp_path / "backtest.csv"
    _write_synthetic_backtest(backtest_path)
    last_mw = _seed_real_matches(tmp_paths, n=MIN_MATCHES_TO_ATTEMPT - 1, home_win_true_rate=0.5)

    result = attempt_recalibration(tmp_paths, backtest_path=backtest_path, matchweek=last_mw, force=True)

    assert result is None
    assert not tmp_paths.recalibration_decisions.exists()
    assert not tmp_paths.active_calibrators.exists()


def test_above_threshold_but_off_cadence_is_a_noop(tmp_paths, tmp_path):
    backtest_path = tmp_path / "backtest.csv"
    _write_synthetic_backtest(backtest_path)
    _seed_real_matches(tmp_paths, n=MIN_MATCHES_TO_ATTEMPT + 10, home_win_true_rate=0.5)
    off_cadence_mw = EVALUATION_CADENCE_MATCHWEEKS + 1  # not a multiple of the cadence

    result = attempt_recalibration(tmp_paths, backtest_path=backtest_path, matchweek=off_cadence_mw)

    assert result is None
    assert not tmp_paths.recalibration_decisions.exists()


def test_on_cadence_matchweek_attempts_and_logs(tmp_paths, tmp_path):
    backtest_path = tmp_path / "backtest.csv"
    _write_synthetic_backtest(backtest_path)
    _seed_real_matches(tmp_paths, n=MIN_MATCHES_TO_ATTEMPT + 10, home_win_true_rate=0.5)
    on_cadence_mw = EVALUATION_CADENCE_MATCHWEEKS * 2

    result = attempt_recalibration(tmp_paths, backtest_path=backtest_path, matchweek=on_cadence_mw)

    assert result is not None
    assert result["decision"] in ("PROMOTED", "REJECTED")
    assert tmp_paths.recalibration_decisions.exists()
    decisions = pd.read_csv(tmp_paths.recalibration_decisions)
    assert len(decisions) == 1
    assert decisions.iloc[0]["decision"] == result["decision"]
    assert decisions.iloc[0]["matchweek"] == on_cadence_mw
    assert decisions.iloc[0]["challenger_method"] == "temperature_scaling"  # n_real << ISOTONIC_MIN_REAL_MATCHES
    if result["decision"] == "REJECTED":
        assert not tmp_paths.active_calibrators.exists()


def test_challenger_with_genuine_signal_gets_promoted_via_bootstrap_ci(tmp_paths, tmp_path):
    backtest_path = tmp_path / "backtest.csv"
    _write_synthetic_backtest(backtest_path, home_win_true_rate=0.5)
    # Real 2026-27 matches home-win far more than the static backtest
    # assumed (0.85 vs 0.5) across many matches -- a challenger that
    # incorporates this should clearly and reliably beat an incumbent
    # stuck on the stale 0.5 belief, across the WHOLE rolling-origin
    # evaluation, not just one lucky slice.
    _seed_real_matches(tmp_paths, n=200, home_win_true_rate=0.85, seed=2)

    result = attempt_recalibration(tmp_paths, backtest_path=backtest_path, force=True)

    assert result is not None
    assert result["decision"] == "PROMOTED"
    assert result["ci_low"] > 0  # the FULL 95% CI favors the challenger, not just the point estimate
    assert result["challenger_method"] == "temperature_scaling"
    assert tmp_paths.active_calibrators.exists()
    with open(tmp_paths.active_calibrators, "rb") as f:
        payload = pickle.load(f)
    assert payload["decision_id"] == result["decision_id"]
    assert payload["challenger"]["method"] == "temperature_scaling"


def test_challenger_without_signal_is_rejected_or_at_least_not_falsely_confident(tmp_paths, tmp_path):
    backtest_path = tmp_path / "backtest.csv"
    # Real matches follow the SAME pattern as the static backtest -- no
    # real signal for a challenger to exploit.
    _write_synthetic_backtest(backtest_path, home_win_true_rate=0.5)
    _seed_real_matches(tmp_paths, n=200, home_win_true_rate=0.5, seed=3)

    result = attempt_recalibration(tmp_paths, backtest_path=backtest_path, force=True)

    assert result is not None
    # With no real exploitable difference, the CI should not reliably
    # favor the challenger -- i.e. it should not be promoted on noise.
    assert result["decision"] == "REJECTED"
    assert not tmp_paths.active_calibrators.exists()


def test_fit_challenger_uses_temperature_scaling_below_isotonic_threshold():
    df = pd.DataFrame({
        "dc_home_win": [0.5] * 50, "dc_draw": [0.3] * 50, "dc_away_win": [0.2] * 50,
        "actual_result": (["home_win"] * 25 + ["draw"] * 15 + ["away_win"] * 10),
    })
    challenger = fit_challenger(df, n_real_matches=ISOTONIC_MIN_REAL_MATCHES - 1)
    assert challenger["method"] == "temperature_scaling"
    assert isinstance(challenger["temperature"], float)


def test_fit_challenger_uses_isotonic_at_or_above_threshold():
    rng = np.random.default_rng(0)
    n = 600
    results = rng.choice(["home_win", "draw", "away_win"], size=n, p=[0.5, 0.3, 0.2])
    df = pd.DataFrame({"dc_home_win": 0.5, "dc_draw": 0.3, "dc_away_win": 0.2, "actual_result": results})
    challenger = fit_challenger(df, n_real_matches=ISOTONIC_MIN_REAL_MATCHES)
    assert challenger["method"] == "isotonic"
    assert "calibrators" in challenger
