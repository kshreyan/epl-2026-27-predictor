import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.models.compute_margin_survival import (  # noqa: E402
    ELIGIBLE_DRAWS_AND,
    margin_buckets,
    percentile_score,
    risk_label,
    verdict,
)
from src.models.scoreline_models import score_matrix  # noqa: E402


def test_margin_buckets_sum_to_one():
    matrix = score_matrix(lam=1.4, mu=1.1, rho=-0.02)
    buckets = margin_buckets(matrix, "home")
    assert sum(buckets.values()) == pytest.approx(1.0, abs=1e-9)
    buckets_away = margin_buckets(matrix, "away")
    assert sum(buckets_away.values()) == pytest.approx(1.0, abs=1e-9)


def test_margin_buckets_home_away_are_mirror_images():
    """A team's own win probability must equal its opponent's lose probability, and vice versa."""
    matrix = score_matrix(lam=1.8, mu=0.9, rho=0.0)
    home = margin_buckets(matrix, "home")
    away = margin_buckets(matrix, "away")
    assert home["win"] == pytest.approx(away["lose_1"] + away["lose_2"] + away["lose_3"] + away["lose_4plus"], abs=1e-9)
    assert home["draw"] == pytest.approx(away["draw"], abs=1e-9)


def test_margin_buckets_lopsided_match_has_large_away_fail_tail():
    """A big home favorite should give the away team a real, non-trivial P(lose by 3+)."""
    matrix = score_matrix(lam=2.5, mu=0.5, rho=0.0)
    away = margin_buckets(matrix, "away")
    p_fail_away = away["lose_3"] + away["lose_4plus"]
    home = margin_buckets(matrix, "home")
    p_fail_home = home["lose_3"] + home["lose_4plus"]
    assert p_fail_away > p_fail_home


def test_eligibility_set_matches_spec():
    assert (0, 1) in ELIGIBLE_DRAWS_AND
    assert (1, 0) in ELIGIBLE_DRAWS_AND
    assert (2, 1) not in ELIGIBLE_DRAWS_AND
    # Draws are eligible via the i == j check in compute_for_league, not this set.
    assert (1, 1) not in ELIGIBLE_DRAWS_AND


@pytest.mark.parametrize(
    "p_fail,expected",
    [
        (0.0, "ELITE +2 SURVIVAL"),
        (0.039, "ELITE +2 SURVIVAL"),
        (0.04, "VERY STRONG"),
        (0.059, "VERY STRONG"),
        (0.06, "STRONG"),
        (0.089, "STRONG"),
        (0.09, "MODERATE"),
        (0.139, "MODERATE"),
        (0.14, "HIGH BLOWOUT RISK"),
        (0.5, "HIGH BLOWOUT RISK"),
    ],
)
def test_risk_label_thresholds(p_fail, expected):
    assert risk_label(p_fail) == expected


def test_percentile_score_favorable_low():
    reference = [1.0, 2.0, 3.0, 4.0, 5.0]
    # A low value among a favorable-low reference should score near 10.
    assert percentile_score(1.0, reference, favorable_low=True) >= 8.0
    # A high value should score near 0.
    assert percentile_score(5.0, reference, favorable_low=True) <= 2.0


def test_percentile_score_empty_reference_is_neutral():
    assert percentile_score(3.0, [], favorable_low=True) == 5.0


def test_verdict_high_risk_is_always_pass_even_with_great_price():
    # A generous price never rescues a High Blowout Risk team -- risk gates first.
    assert verdict("HIGH BLOWOUT RISK", 0.30) == "PASS"
    assert verdict("HIGH BLOWOUT RISK", None) == "PASS"


def test_verdict_safe_tier_with_fair_or_better_price_is_pick():
    assert verdict("ELITE +2 SURVIVAL", None) == "PICK +2"
    assert verdict("VERY STRONG", 0.01) == "PICK +2"
    assert verdict("STRONG", -0.02) == "PICK +2"


def test_verdict_safe_tier_with_bad_price_is_not_a_free_pick():
    assert verdict("STRONG", -0.10) == "PASS"


def test_verdict_moderate_tier_needs_nonnegative_value():
    assert verdict("MODERATE", None) == "LEAN +2"
    assert verdict("MODERATE", 0.01) == "LEAN +2"
    assert verdict("MODERATE", -0.10) == "PASS"


def test_verdict_large_negative_value_gap_is_always_pass():
    assert verdict("ELITE +2 SURVIVAL", -0.06) == "PASS"


MARGIN_SURVIVAL_PATH = REPO_ROOT / "data" / "outputs" / "epl_2026_27_margin_survival.csv"

pytestmark_margin = pytest.mark.skipif(not MARGIN_SURVIVAL_PATH.exists(), reason="run compute_margin_survival.py first")


@pytestmark_margin
def test_published_margin_survival_probabilities_sum_correctly():
    df = pd.read_csv(MARGIN_SURVIVAL_PATH)
    total = df["win_prob"] + df["draw_prob"] + df["lose_1_prob"] + df["lose_2_prob"] + df["lose_3_prob"] + df["lose_4plus_prob"]
    assert np.allclose(total, 1.0, atol=1e-3)
    assert np.allclose(df["p_cover"] + df["p_push"] + df["p_fail"], 1.0, atol=1e-3)


@pytestmark_margin
def test_published_home_away_rows_are_mirror_pairs():
    df = pd.read_csv(MARGIN_SURVIVAL_PATH)
    for match_id, group in df.groupby("match_id"):
        if len(group) != 2:
            continue
        home_row = group[group["is_home"]].iloc[0]
        away_row = group[~group["is_home"]].iloc[0]
        # Values are rounded to 4dp on write, so allow for that -- this
        # checks the mirror-image invariant survives real CSV rounding,
        # not floating-point-perfect equality.
        assert home_row["win_prob"] == pytest.approx(away_row["lose_1_prob"] + away_row["lose_2_prob"] + away_row["lose_3_prob"] + away_row["lose_4plus_prob"], abs=4e-4)


@pytestmark_margin
def test_published_margin_survival_has_no_eligibility_filter():
    """Every team in every match gets a row -- not just eligible ones."""
    df = pd.read_csv(MARGIN_SURVIVAL_PATH)
    assert (~df["eligible"]).any(), "expected at least one non-eligible match to still be published"
    assert set(df["verdict"].unique()) <= {"PICK +2", "LEAN +2", "PASS"}
