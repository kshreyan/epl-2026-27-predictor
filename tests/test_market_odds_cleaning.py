import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.features.build_market_features import (  # noqa: E402
    build_market_features,
    log_odds_average,
    log_odds_average_binary,
    overround,
    remove_overround,
    remove_overround_binary,
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


def test_remove_overround_binary_sums_to_one():
    probs = remove_overround_binary((1.8, 2.1))  # a real-shaped Asian Handicap quote
    assert abs(sum(probs) - 1.0) < 1e-9
    assert all(p > 0 for p in probs)


def test_log_odds_average_binary_matches_single_source_when_only_one_given():
    assert log_odds_average_binary([0.5106]) == pytest.approx(0.5106, abs=1e-6)


def test_log_odds_average_binary_of_two_sources_is_between_them():
    a, b = 0.40, 0.60
    blended = log_odds_average_binary([a, b])
    assert a < blended < b


def test_market_features_marks_sentinel_only_matches_unavailable():
    # A match with only sentinel (is_real_data=False) odds rows must come
    # back market_available=False -- never a fabricated "probability"
    # computed from placeholder odds.
    odds_df = pd.DataFrame([{
        "match_id": "m1", "is_real_data": False, "current_home_odds": "", "current_draw_odds": "", "current_away_odds": "",
    }])
    features = build_market_features(odds_df)
    assert (features["market_available"] == False).all()  # noqa: E712


def test_market_features_uses_real_odds_when_present():
    # A match with real (is_real_data=True) bookmaker rows must come back
    # market_available=True with a genuine no-vig probability -- this is
    # what a real live-odds feed (collect_odds.py with ODDS_API_KEY
    # configured) actually produces once a bookmaker posts a market.
    odds_df = pd.DataFrame([
        {"match_id": "m2", "is_real_data": True, "current_home_odds": 1.5, "current_draw_odds": 4.0, "current_away_odds": 6.0},
        {"match_id": "m2", "is_real_data": True, "current_home_odds": 1.55, "current_draw_odds": 3.9, "current_away_odds": 5.8},
    ])
    features = build_market_features(odds_df)
    row = features[features["match_id"] == "m2"].iloc[0]
    assert row["market_available"] == True  # noqa: E712
    assert 0 < row["market_home_win_prob_current"] < 1
    total = row["market_home_win_prob_current"] + row["market_draw_prob_current"] + row["market_away_win_prob_current"]
    assert abs(total - 1.0) < 1e-6


def test_market_features_on_real_odds_file_never_fabricates():
    # Whatever the CURRENT real state of the file is (sentinel-only, or
    # partially real once a live feed is connected), every row's
    # market_available must be a true reflection of is_real_data --
    # never computed from a sentinel row. build_market_features is
    # 1X2-only, so the relevant real rows are specifically market_type
    # == "h2h" -- the file also carries real "spreads"/"totals" rows
    # (see collect_odds.py) whose coverage can genuinely diverge from
    # h2h's (bookmakers post each market independently).
    if not RAW_ODDS_PATH.exists():
        return
    odds_df = pd.read_csv(RAW_ODDS_PATH)
    features = build_market_features(odds_df)
    is_h2h = odds_df["market_type"] == "h2h" if "market_type" in odds_df.columns else True
    real_match_ids = set(odds_df.loc[(odds_df["is_real_data"] == True) & is_h2h, "match_id"])  # noqa: E712
    for _, row in features.iterrows():
        assert row["market_available"] == (row["match_id"] in real_match_ids)
