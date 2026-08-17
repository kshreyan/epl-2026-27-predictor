import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

INJURY_RAW_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_injury_suspension.csv"
PREDICTIONS_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"


def test_injury_raw_rows_are_unknown_not_healthy():
    """Spec rule: missing injury data must NOT be treated as 'fully
    healthy'. The sentinel file must say availability_status=unknown,
    never available."""
    df = pd.read_csv(INJURY_RAW_PATH)
    assert (df["availability_status"] == "unknown").all()
    assert (df["is_real_data"] == False).all()  # noqa: E712


def test_injury_raw_covers_every_2026_27_club():
    from src.utils.team_names import EPL_2026_27_CLUBS
    df = pd.read_csv(INJURY_RAW_PATH)
    assert set(df["team"]) == set(EPL_2026_27_CLUBS)


@pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")
def test_predictions_flag_injury_data_as_unavailable():
    """Every 2026-27 prediction must explicitly flag injury_data_available
    =False rather than silently proceeding as if health status were known."""
    df = pd.read_csv(PREDICTIONS_PATH)
    assert (df["injury_data_available"] == False).all()  # noqa: E712
