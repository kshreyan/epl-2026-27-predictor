"""NFL calibration, reusing calibrate_probabilities.py's isotonic
machinery (now generalized to a configurable class list and raw-
probability column prefix -- see that module) rather than duplicating
it. Calibrates the real point-margin model's own `pm_home_win`/
`pm_away_win` columns (nfl_backtest_match_results.csv) against real
historical outcomes.

Real ties are excluded from calibration (not from the moneyline model
itself, which still produces a real `pm_draw` -- see
point_margin_model.py): a ~0.3% real event has too few real positive
examples for isotonic regression to calibrate meaningfully, and the
two displayed win probabilities are what this real calibration check
is about.

Run: python -m src.calibration.calibrate_nfl_probabilities
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.calibration.calibrate_probabilities import (  # noqa: E402
    MIN_SAMPLES_FOR_ISOTONIC,
    N_BINS,
    _reliability_table,
    apply_calibration,
    expected_calibration_error,
    fit_calibrators,
)
from src.utils.versioning import now_utc_iso  # noqa: E402

CLASSES = ["home_win", "away_win"]
RAW_PREFIX = "pm_"


def main(league_id: str = "nfl") -> None:
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    backtest_df = pd.read_csv(backtest_path)
    backtest_df = backtest_df[backtest_df["actual_result"] != "draw"].reset_index(drop=True)

    calibrators = fit_calibrators(backtest_df, classes=CLASSES, raw_col_prefix=RAW_PREFIX)
    method_used = "isotonic" if all(c is not None for c in calibrators.values()) else "raw_fallback_insufficient_samples"

    ece = expected_calibration_error(backtest_df, calibrators, classes=CLASSES, raw_col_prefix=RAW_PREFIX)
    raw_log_loss = backtest_df["pm_log_loss"].mean()

    calibrated_losses = []
    for _, row in backtest_df.iterrows():
        raw_probs = {cls: row[f"{RAW_PREFIX}{cls}"] for cls in CLASSES}
        cal_probs = apply_calibration(calibrators, raw_probs, classes=CLASSES)
        p = max(cal_probs[row["actual_result"]], 1e-12)
        calibrated_losses.append(-np.log(p))
    calibrated_log_loss = float(np.mean(calibrated_losses))

    out_dir = REPO_ROOT / "data" / "outputs"
    reliability_tables = pd.concat(
        [_reliability_table(backtest_df, cls, raw_col_prefix=RAW_PREFIX) for cls in CLASSES], ignore_index=True,
    )
    reliability_tables.to_csv(out_dir / f"{league_id}_2026_27_reliability_tables.csv", index=False)

    pd.DataFrame([{
        "method": method_used, "ece": round(ece, 4),
        "raw_log_loss": round(float(raw_log_loss), 4), "calibrated_log_loss": round(calibrated_log_loss, 4),
        "n_matches": len(backtest_df), "generated_at": now_utc_iso(),
    }]).to_csv(out_dir / f"{league_id}_2026_27_calibration_summary.csv", index=False)

    report_path = REPO_ROOT / "reports" / f"{league_id}_calibration_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} Calibration Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(f"Calibration method: **{method_used}** (isotonic regression per outcome class, fit on "
                f"{len(backtest_df)} real non-tie backtest games; minimum {MIN_SAMPLES_FOR_ISOTONIC} real "
                f"samples required).\n\n")
        f.write(f"- Raw point-margin-model mean log loss: {raw_log_loss:.4f}\n")
        f.write(f"- Calibrated mean log loss: {calibrated_log_loss:.4f}\n")
        f.write(f"- Expected Calibration Error ({N_BINS} bins): {ece:.4f}\n")
    print(f"Wrote calibration report ({method_used}, ECE={ece:.4f}) to {report_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nfl", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
