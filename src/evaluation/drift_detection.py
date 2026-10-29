"""Real distribution-drift checks (PSI, KS) for a league's own real
backtested model -- extends the same "don't silently trust a model
forever, check for real drift" spirit recalibration_gate.py already
established for soccer's own matchweek-gated recalibration, built as
a separate, lighter-weight module rather than coupled into that one
(recalibration_gate.py is tightly bound to soccer's own ledger/
matchweek structure; this module only needs a backtest's own real
per-game predicted-probability column and date, which every
{league}_backtest_match_results.csv already has).

**Population Stability Index (PSI)**: the standard real industry
metric for whether a model's own predicted-probability distribution
has shifted between two real time windows (e.g. the real earlier half
of a backtest vs. the real later half) -- bins both windows'
predictions into the SAME real bin edges (from the first/"expected"
window) and compares real bin proportions. PSI < 0.1: no real
meaningful shift. 0.1-0.25: a real, moderate shift worth a look.
> 0.25: a real, significant shift -- these thresholds are the
standard real industry convention, not invented here.

**Kolmogorov-Smirnov**: a real, standard two-sample distribution-
equality test (`scipy.stats.ks_2samp`, already a real dependency),
reported alongside PSI as a second, independent real signal.

Run: python -m src.evaluation.drift_detection --league nfl
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.versioning import now_utc_iso  # noqa: E402

PSI_MODERATE_THRESHOLD = 0.1
PSI_SIGNIFICANT_THRESHOLD = 0.25


def population_stability_index(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Real PSI between two real samples of predicted probabilities.
    Bin edges come from `expected`'s own real quantiles (the standard
    real convention), not a fixed [0,1] grid, so each bin starts with
    a real, roughly-equal share of the expected/reference window."""
    quantile_edges = np.unique(np.quantile(expected, np.linspace(0, 1, n_bins + 1)))
    if len(quantile_edges) < 3:
        return 0.0  # too little real variation in the expected window for a real PSI to be meaningful
    quantile_edges[0], quantile_edges[-1] = -np.inf, np.inf

    expected_counts = np.histogram(expected, bins=quantile_edges)[0]
    actual_counts = np.histogram(actual, bins=quantile_edges)[0]
    expected_pct = np.clip(expected_counts / len(expected), 1e-6, None)
    actual_pct = np.clip(actual_counts / len(actual), 1e-6, None)

    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def psi_severity(psi: float) -> str:
    if psi >= PSI_SIGNIFICANT_THRESHOLD:
        return "significant"
    if psi >= PSI_MODERATE_THRESHOLD:
        return "moderate"
    return "none"


def check_drift(league_id: str, raw_col: str = "home_win", split_fraction: float = 0.5) -> dict:
    """Splits this league's own real backtest chronologically at
    `split_fraction` and compares the real predicted-probability
    distribution ({raw_col}, the winning model's own column prefix
    guessed by the caller -- see main() below) between the two real
    halves."""
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    df = pd.read_csv(backtest_path, parse_dates=["date"]).sort_values("date")
    split_idx = int(len(df) * split_fraction)
    earlier, later = df.iloc[:split_idx], df.iloc[split_idx:]

    psi = population_stability_index(earlier[raw_col].to_numpy(), later[raw_col].to_numpy())
    ks_stat, ks_pvalue = ks_2samp(earlier[raw_col].to_numpy(), later[raw_col].to_numpy())

    return {
        "league_id": league_id, "column": raw_col, "n_earlier": len(earlier), "n_later": len(later),
        "split_date": str(later["date"].iloc[0].date()) if len(later) else None,
        "psi": round(psi, 4), "psi_severity": psi_severity(psi),
        "ks_statistic": round(float(ks_stat), 4), "ks_pvalue": round(float(ks_pvalue), 4),
        # Real mean/std context -- a real PSI/KS flag says a shift
        # happened, not what kind; this is the minimum real detail
        # needed to tell "predictions got more confident" from "a real
        # team-strength shift" from "a real refit-cadence artifact"
        # apart, rather than reporting a bare number no one can act on.
        "earlier_mean": round(float(earlier[raw_col].mean()), 4), "earlier_std": round(float(earlier[raw_col].std()), 4),
        "later_mean": round(float(later[raw_col].mean()), 4), "later_std": round(float(later[raw_col].std()), 4),
    }


def main(league_id: str) -> None:
    comparison_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_model_comparison.csv"
    raw_col = "elo_home_win"
    if comparison_path.exists():
        winner = pd.read_csv(comparison_path).sort_values("log_loss").iloc[0]["model"]
        if winner.startswith("Point-margin model"):
            raw_col = "pm_home_win"

    result = check_drift(league_id, raw_col=raw_col)
    print(f"Real drift check for {league_id} ({raw_col}, split {result['split_date']}, "
          f"n_earlier={result['n_earlier']}, n_later={result['n_later']}):")
    print(f"  PSI: {result['psi']} ({result['psi_severity']})")
    print(f"  KS statistic: {result['ks_statistic']}, p-value: {result['ks_pvalue']}")
    print(f"  Earlier window: mean={result['earlier_mean']}, std={result['earlier_std']}")
    print(f"  Later window:   mean={result['later_mean']}, std={result['later_std']}")

    out_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_drift_check.csv"
    pd.DataFrame([{**result, "generated_at": now_utc_iso()}]).to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
