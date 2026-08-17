import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

POSITION_DIST_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_position_distribution.csv"
EXPECTED_TABLE_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_expected_table.csv"

pytestmark = pytest.mark.skipif(not POSITION_DIST_PATH.exists(), reason="run the simulation pipeline first")


def test_finish_probabilities_are_between_0_and_1():
    df = pd.read_csv(POSITION_DIST_PATH)
    finish_cols = [c for c in df.columns if c.startswith("finish_")]
    for c in finish_cols:
        assert (df[c] >= 0).all()
        assert (df[c] <= 1).all()


def test_sum_of_title_probabilities_is_approximately_one():
    df = pd.read_csv(POSITION_DIST_PATH)
    assert abs(df["finish_1_probability"].sum() - 1.0) < 0.02


def test_sum_of_relegation_probabilities_is_approximately_three():
    df = pd.read_csv(POSITION_DIST_PATH)
    relegation_cols = ["finish_18_probability", "finish_19_probability", "finish_20_probability"]
    assert abs(df[relegation_cols].sum().sum() - 3.0) < 0.05


def test_expected_table_probabilities_internally_consistent():
    df = pd.read_csv(EXPECTED_TABLE_PATH)
    assert (df["top_4_probability"] <= df["top_5_probability"] + 1e-6).all()
    assert (df["top_4_probability"] <= df["top_half_probability"] + 1e-6).all()
    assert (df["title_probability"] <= df["top_4_probability"] + 1e-6).all()
