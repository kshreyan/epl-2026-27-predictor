"""Tests the markets tail-risk engine's core real math: EWMA
volatility (RiskMetrics-style) and the risk-tier assignment -- the
markets equivalent of soccer's risk_label()/compute_margin_survival.py
tests."""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_market_tail_risk import ewma_daily_vol  # noqa: E402
from src.markets import all_market_ids, load_market_config  # noqa: E402
from src.models.compute_market_tail_risk import RISK_LABELS, THRESHOLD, _risk_label  # noqa: E402


def test_ewma_vol_is_positive_for_nonzero_returns():
    returns = np.array([0.01, -0.02, 0.015, -0.01, 0.02])
    assert ewma_daily_vol(returns) > 0


def test_ewma_vol_is_zero_for_all_zero_returns():
    returns = np.zeros(10)
    assert ewma_daily_vol(returns) == pytest.approx(0.0)


def test_ewma_vol_weights_recent_returns_more_heavily():
    # A real recent large move should raise the EWMA estimate more than
    # the same-sized move placed far in the past (lambda < 1 -- the
    # whole point of using EWMA over a flat rolling average).
    recent_shock = np.array([0.001] * 50 + [0.10])
    old_shock = np.array([0.10] + [0.001] * 50)
    assert ewma_daily_vol(recent_shock) > ewma_daily_vol(old_shock)


def test_ewma_vol_matches_hand_computed_two_point_case():
    # lambda=0.94, returns=[r0, r1]: weights (unnormalized) are
    # (1-lam)*lam^1, (1-lam)*lam^0 -- i.e. r1 (most recent) gets more
    # weight than r0.
    lam = 0.94
    r0, r1 = 0.02, -0.03
    w0, w1 = (1 - lam) * lam, (1 - lam) * lam**0
    w0, w1 = w0 / (w0 + w1), w1 / (w0 + w1)
    expected = np.sqrt(w0 * r0**2 + w1 * r1**2)
    assert ewma_daily_vol(np.array([r0, r1]), lam=lam) == pytest.approx(expected)


def test_risk_label_boundaries_for_us_equities():
    cutoffs = RISK_LABELS["us_equities"]
    # Just under each real cutoff -> that tier; just at/over -> the next one.
    assert _risk_label("us_equities", 0.0) == "ELITE SURVIVAL"
    for cutoff, label in cutoffs[:-1]:
        assert _risk_label("us_equities", cutoff - 1e-6) == label
    assert _risk_label("us_equities", 10.0) == "HIGH BLOWOUT RISK"


def test_risk_labels_are_five_tiers_in_ascending_cutoff_order():
    labels = [l for _, l in RISK_LABELS["us_equities"]]
    assert labels == ["ELITE SURVIVAL", "VERY STRONG", "STRONG", "MODERATE", "HIGH BLOWOUT RISK"]
    cutoffs = [c for c, _ in RISK_LABELS["us_equities"]]
    assert cutoffs == sorted(cutoffs)


def test_every_registered_market_has_a_real_threshold_and_risk_labels():
    # Guards against adding a new markets.yaml entry without also
    # giving it its own real backtested THRESHOLD/RISK_LABELS (see
    # compute_market_tail_risk.py's module docstring -- never copy
    # another market's row).
    for market_id in all_market_ids():
        assert market_id in THRESHOLD, f"{market_id} has no real backtested THRESHOLD yet"
        assert market_id in RISK_LABELS, f"{market_id} has no real backtested RISK_LABELS yet"


def test_markets_registry_loads_us_equities():
    cfg = load_market_config("us_equities")
    assert cfg.country == "USA"
    assert cfg.asset_class == "equities"
    assert len(cfg.tickers) == 30
    assert len(set(cfg.tickers)) == 30  # no real duplicate tickers
