"""Tests the real PSI/KS drift-detection functions: an identical
distribution must show ~0 real drift, and a genuinely shifted real
distribution must be flagged."""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.drift_detection import (  # noqa: E402
    PSI_MODERATE_THRESHOLD,
    PSI_SIGNIFICANT_THRESHOLD,
    population_stability_index,
    psi_severity,
)


def test_identical_distributions_have_near_zero_psi():
    rng = np.random.default_rng(42)
    sample = rng.uniform(0, 1, 2000)
    expected, actual = sample[:1000], sample[1000:]
    psi = population_stability_index(expected, actual)
    assert abs(psi) < 0.05


def test_shifted_distribution_has_real_meaningful_psi():
    rng = np.random.default_rng(42)
    expected = rng.uniform(0, 1, 1000)
    actual = rng.uniform(0.4, 1, 1000)  # a real, substantial shift toward higher values
    psi = population_stability_index(expected, actual)
    assert psi >= PSI_MODERATE_THRESHOLD


def test_psi_severity_buckets():
    assert psi_severity(0.05) == "none"
    assert psi_severity(0.15) == "moderate"
    assert psi_severity(0.30) == "significant"
    assert psi_severity(PSI_MODERATE_THRESHOLD) == "moderate"
    assert psi_severity(PSI_SIGNIFICANT_THRESHOLD) == "significant"


def test_psi_is_symmetric_in_direction_of_shift():
    rng = np.random.default_rng(7)
    low = rng.uniform(0, 0.5, 1000)
    high = rng.uniform(0.5, 1, 1000)
    psi_up = population_stability_index(low, high)
    psi_down = population_stability_index(high, low)
    assert psi_up > PSI_MODERATE_THRESHOLD
    assert psi_down > PSI_MODERATE_THRESHOLD


def test_too_few_unique_values_returns_zero_not_a_crash():
    constant = np.full(100, 0.5)
    assert population_stability_index(constant, constant) == 0.0
