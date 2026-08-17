import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

PREDICTIONS_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv"

pytestmark = pytest.mark.skipif(not PREDICTIONS_PATH.exists(), reason="run the prediction pipeline first")


def test_predicted_result_matches_predicted_score():
    df = pd.read_csv(PREDICTIONS_PATH)
    for _, row in df.iterrows():
        home_g, away_g = row["predicted_score_model_only"].split("-")
        home_g, away_g = int(home_g), int(away_g)
        expected_result = "home_win" if home_g > away_g else ("away_win" if home_g < away_g else "draw")
        assert row["predicted_result_model_only"] == expected_result, (
            f"{row['match_id']}: score {row['predicted_score_model_only']} "
            f"implies {expected_result}, got {row['predicted_result_model_only']}"
        )
