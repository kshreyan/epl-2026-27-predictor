"""NCAA Football calibration, reusing calibrate_probabilities.py's
generalized isotonic machinery (see calibrate_nfl_probabilities.py/
calibrate_nba_probabilities.py for the same pattern). Calibrates the
real Elo-only model's own `elo_home_win`/`elo_away_win` columns
(ncaaf_backtest_match_results.csv) -- this league's own real
moneyline backtest winner (see reports/ncaaf_model_selection_report
.md; the point-margin model, including its real conference-aware
variant, loses the overall moneyline comparison even though the
conference-aware variant wins the narrower real margin-prediction
task -- see predict_team_sport_matches.py's own wiring). NCAA Football
has no real tie outcome (confirmed directly, same reasoning as NFL/
NBA -- see point_margin_model.py's module docstring), so every real
row is already a clean 2-class case.

Run: python -m src.calibration.calibrate_ncaaf_probabilities
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
RAW_PREFIX = "elo_"


def main(league_id: str = "ncaaf") -> None:
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    backtest_df = pd.read_csv(backtest_path)

    calibrators = fit_calibrators(backtest_df, classes=CLASSES, raw_col_prefix=RAW_PREFIX)
    method_used = "isotonic" if all(c is not None for c in calibrators.values()) else "raw_fallback_insufficient_samples"

    ece = expected_calibration_error(backtest_df, calibrators, classes=CLASSES, raw_col_prefix=RAW_PREFIX)
    raw_log_loss = backtest_df["elo_log_loss"].mean()

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
                f"{len(backtest_df)} real backtest games; minimum {MIN_SAMPLES_FOR_ISOTONIC} real "
                f"samples required).\n\n")
        f.write(f"- Raw Elo-only mean log loss: {raw_log_loss:.4f}\n")
        f.write(f"- Calibrated mean log loss: {calibrated_log_loss:.4f}\n")
        f.write(f"- Expected Calibration Error ({N_BINS} bins): {ece:.4f}\n")
    print(f"Wrote calibration report ({method_used}, ECE={ece:.4f}) to {report_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="ncaaf", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
