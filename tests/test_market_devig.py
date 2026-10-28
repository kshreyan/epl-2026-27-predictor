"""Tests Shin's method and the power method de-vig implementations:
each must return valid probabilities that sum to 1, agree with
proportional normalization when there's no real overround to remove,
and actually shrink the overround for a real-shaped two-sided book."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.features.market_devig import DEVIG_METHODS, devig_power, devig_shin  # noqa: E402

# A real-shaped two-outcome book: -150/+130 American converted to
# decimal odds (1.667 / 2.30), ~4.7% overround -- typical real
# moneyline vig, not an extreme/contrived case.
REALISTIC_ODDS = (1.667, 2.30)


@pytest.mark.parametrize("devig_fn", [devig_shin, devig_power])
def test_devig_methods_sum_to_one(devig_fn):
    fair = devig_fn(REALISTIC_ODDS)
    assert sum(fair) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("devig_fn", [devig_shin, devig_power])
def test_devig_methods_return_valid_probabilities(devig_fn):
    fair = devig_fn(REALISTIC_ODDS)
    assert all(0.0 < p < 1.0 for p in fair)


@pytest.mark.parametrize("devig_fn", [devig_shin, devig_power])
def test_devig_methods_preserve_favorite_ordering(devig_fn):
    fair = devig_fn(REALISTIC_ODDS)
    assert fair[0] > fair[1]  # shorter decimal odds (1.667) is the real favorite


@pytest.mark.parametrize("devig_fn", [devig_shin, devig_power])
def test_devig_methods_reduce_to_proportional_at_zero_overround(devig_fn):
    fair_book_odds = (2.0, 2.0)  # exactly 0% overround
    fair = devig_fn(fair_book_odds)
    assert fair[0] == pytest.approx(0.5, abs=1e-6)
    assert fair[1] == pytest.approx(0.5, abs=1e-6)


def test_devig_methods_agree_closely_for_a_small_realistic_overround():
    # All three real methods should land close together for a modest,
    # realistic overround -- they're meant to diverge more at larger
    # overrounds/more lopsided books, not wildly disagree here.
    shin = devig_shin(REALISTIC_ODDS)
    power = devig_power(REALISTIC_ODDS)
    multiplicative = DEVIG_METHODS["multiplicative"](REALISTIC_ODDS)
    assert shin[0] == pytest.approx(multiplicative[0], abs=0.01)
    assert power[0] == pytest.approx(multiplicative[0], abs=0.01)


def test_devig_methods_handle_three_outcome_markets():
    # A real 1X2-shaped book (home/draw/away), confirms the n-outcome
    # (not just binary) solver path works.
    odds_1x2 = (2.10, 3.40, 3.60)
    for devig_fn in (devig_shin, devig_power):
        fair = devig_fn(odds_1x2)
        assert len(fair) == 3
        assert sum(fair) == pytest.approx(1.0, abs=1e-6)
        assert fair[0] > fair[1]  # home is the real favorite here
