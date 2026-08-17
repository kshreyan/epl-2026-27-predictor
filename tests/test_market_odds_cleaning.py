import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.features.build_market_features import (  # noqa: E402
    build_market_features,
    log_odds_average,
    overround,
    remove_overround,
)

RAW_ODDS_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv"


def test_remove_overround_sums_to_one():
    # A typical round of 1X2 odds with a ~5% bookmaker margin
    probs = remove_overround((2.0, 3.5, 4.0))
    assert abs(sum(probs) - 1.0) < 1e-9
    assert all(p > 0 for p in probs)


def test_overround_is_positive_for_a_real_bookmaker_book():
    # Raw implied probabilities from these odds sum to > 1 (the vig)
    assert overround((2.0, 3.5, 4.0)) > 0


def test_overround_is_zero_for_a_fair_book():
    # Odds chosen so 1/o sums to exactly 1 (a "fair" book with no margin)
    assert abs(overround((2.0, 4.0, 4.0))) < 1e-9


def test_log_odds_average_matches_single_bookmaker_when_only_one_given():
    single = (0.5, 0.3, 0.2)
    result = log_odds_average([single])
    assert all(abs(a - b) < 1e-6 for a, b in zip(result, single))


def test_log_odds_average_of_multiple_bookmakers_sums_to_one():
    result = log_odds_average([(0.5, 0.3, 0.2), (0.45, 0.32, 0.23), (0.52, 0.28, 0.20)])
    assert abs(sum(result) - 1.0) < 1e-9


def test_market_features_report_unavailable_for_current_sentinel_odds_file():
    # data/raw/epl_2026_27_real_odds.csv is a Phase-1/2 sentinel file (no
    # live feed connected) -- every row must come back market_available=False
    # rather than silently computing "probabilities" from fabricated data.
    odds_df = pd.read_csv(RAW_ODDS_PATH)
    features = build_market_features(odds_df)
    assert (features["market_available"] == False).all()  # noqa: E712
