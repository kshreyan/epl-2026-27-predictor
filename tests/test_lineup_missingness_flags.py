import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

PREDICTIONS_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"

pytestmark = pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")


def test_predictions_flag_lineup_data_as_unavailable():
    """Spec rule: missing lineup data must NOT be treated as 'strongest
    XI'. No expected/confirmed-lineup source is connected in Phase 1/2,
    so every prediction must say lineup_data_available=False."""
    df = pd.read_csv(PREDICTIONS_PATH)
    assert (df["lineup_data_available"] == False).all()  # noqa: E712


def test_lineup_strength_fields_are_blank_not_fabricated():
    df = pd.read_csv(PREDICTIONS_PATH)
    assert df["home_expected_lineup_strength"].isna().all()
    assert df["away_expected_lineup_strength"].isna().all()


def test_predictions_flag_squad_data_as_unavailable():
    df = pd.read_csv(PREDICTIONS_PATH)
    assert (df["squad_data_available"] == False).all()  # noqa: E712
