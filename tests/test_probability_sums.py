import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

PREDICTIONS_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"
EXPECTED_TABLE_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_expected_table.csv"
POSITION_DIST_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_position_distribution.csv"

pytestmark = pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")


def test_match_probabilities_sum_to_one():
    df = pd.read_csv(PREDICTIONS_PATH)
    total = df["home_win_prob_model_only"] + df["draw_prob_model_only"] + df["away_win_prob_model_only"]
    assert (total.sub(1.0).abs() < 1e-3).all()


def test_top10_scorelines_valid_json_and_nonneg_probs():
    df = pd.read_csv(PREDICTIONS_PATH)
    for raw in df["top_10_scorelines_model_only_json"].head(20):
        scorelines = json.loads(raw)
        assert len(scorelines) == 10
        for s in scorelines:
            assert s["probability"] >= 0
            assert "-" in s["score"]


@pytest.mark.skipif(not POSITION_DIST_PATH.exists(), reason="run the simulation pipeline first")
def test_position_distribution_sums_to_one_per_team():
    df = pd.read_csv(POSITION_DIST_PATH)
    finish_cols = [c for c in df.columns if c.startswith("finish_")]
    assert len(finish_cols) == 20
    totals = df[finish_cols].sum(axis=1)
    assert (totals.sub(1.0).abs() < 1e-2).all()


@pytest.mark.skipif(not EXPECTED_TABLE_PATH.exists(), reason="run the simulation pipeline first")
def test_expected_table_has_all_20_teams():
    df = pd.read_csv(EXPECTED_TABLE_PATH)
    assert len(df) == 20
    assert df["team"].duplicated().sum() == 0
