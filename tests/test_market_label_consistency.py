"""Published predictions never contradict their own market flags, in any
league. Guards against the pre-1b4467f mislabel coming back: rows with
market_blend_applied=True but market_available=False and the blended
probability filed under *_model_only (repaired in place for already-
locked rows by scripts/repair_pre_fix_blend_labels.py)."""
from pathlib import Path

import pandas as pd
import pytest

OUT = Path(__file__).resolve().parents[1] / "data" / "outputs"
PREDICTION_FILES = sorted(OUT.glob("*_2026_27_match_predictions.csv"))
INTEGRATED = ["home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated"]


@pytest.mark.skipif(not PREDICTION_FILES, reason="no prediction outputs generated yet")
@pytest.mark.parametrize("path", PREDICTION_FILES, ids=lambda p: p.name.split("_2026_27")[0])
def test_blend_implies_real_market_and_integrated_probs(path):
    df = pd.read_csv(path)
    if "market_blend_applied" not in df.columns:
        pytest.skip("league has no market blend columns")
    blended = df["market_blend_applied"] == True  # noqa: E712
    contradictions = df.loc[blended & (df["market_available"] != True), "match_id"]  # noqa: E712
    assert contradictions.empty, f"blend applied without market_available: {list(contradictions)[:5]}"
    if set(INTEGRATED) <= set(df.columns):
        missing = df.loc[blended & df[INTEGRATED].isna().any(axis=1), "match_id"]
        assert missing.empty, f"blend applied but market-integrated probabilities blank: {list(missing)[:5]}"
