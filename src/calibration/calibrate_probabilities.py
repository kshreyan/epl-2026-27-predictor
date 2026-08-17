"""Isotonic probability calibration, fit on real backtest predictions.

Raw Dixon-Coles win/draw/loss probabilities are not guaranteed to be
well-calibrated (e.g. the model may be systematically over- or
under-confident on favorites). We fit one isotonic regressor per
outcome class (home_win/draw/away_win) mapping raw predicted
probability -> empirical frequency of that outcome in the real
backtest, using `data/outputs/epl_backtest_match_results.csv`
(src/evaluation/backtest.py output). Calibrated probabilities are then
renormalized to sum to 1 across the three classes.

Run: python -m src.calibration.calibrate_probabilities
(requires backtest to have been run first)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
OUT_REPORT = REPO_ROOT / "data" / "outputs" / "epl_2026_27_calibration_report.md"
OUT_RELIABILITY = REPO_ROOT / "data" / "outputs" / "epl_2026_27_reliability_tables.csv"
OUT_CURVES = REPO_ROOT / "data" / "outputs" / "epl_2026_27_calibration_curves.csv"

CLASSES = ["home_win", "draw", "away_win"]
N_BINS = 10
MIN_SAMPLES_FOR_ISOTONIC = 500


def fit_calibrators(backtest_df: pd.DataFrame) -> dict[str, IsotonicRegression | None]:
    calibrators = {}
    for cls in CLASSES:
        raw = backtest_df[f"dc_{_col_suffix(cls)}"]
        target = (backtest_df["actual_result"] == cls).astype(int)
        if len(backtest_df) < MIN_SAMPLES_FOR_ISOTONIC:
            calibrators[cls] = None  # not enough data: fall back to raw probabilities
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(raw, target)
        calibrators[cls] = iso
    return calibrators


def _col_suffix(cls: str) -> str:
    return {"home_win": "home_win", "draw": "draw", "away_win": "away_win"}[cls]


def apply_calibration(calibrators: dict, raw_probs: dict[str, float]) -> dict[str, float]:
    calibrated = {}
    for cls in CLASSES:
        cal = calibrators.get(cls)
        raw = raw_probs[cls]
        calibrated[cls] = float(cal.predict([raw])[0]) if cal is not None else raw
    total = sum(calibrated.values())
    if total <= 0:
        return {cls: 1 / 3 for cls in CLASSES}
    return {cls: v / total for cls, v in calibrated.items()}


def _reliability_table(backtest_df: pd.DataFrame, cls: str) -> pd.DataFrame:
    raw = backtest_df[f"dc_{_col_suffix(cls)}"]
    target = (backtest_df["actual_result"] == cls).astype(int)
    bins = np.linspace(0, 1, N_BINS + 1)
    bin_idx = np.clip(np.digitize(raw, bins) - 1, 0, N_BINS - 1)
    rows = []
    for b in range(N_BINS):
        mask = bin_idx == b
        n = int(mask.sum())
        rows.append({
            "outcome_class": cls,
            "bin_lower": round(bins[b], 2),
            "bin_upper": round(bins[b + 1], 2),
            "n_matches": n,
            "mean_predicted_probability": round(float(raw[mask].mean()), 4) if n else "",
            "empirical_frequency": round(float(target[mask].mean()), 4) if n else "",
        })
    return pd.DataFrame(rows)


def expected_calibration_error(backtest_df: pd.DataFrame, calibrators: dict) -> float:
    """ECE on the top predicted class, using calibrated probabilities."""
    errors, weights = [], []
    for _, row in backtest_df.iterrows():
        raw_probs = {cls: row[f"dc_{_col_suffix(cls)}"] for cls in CLASSES}
        cal_probs = apply_calibration(calibrators, raw_probs)
        top_cls = max(cal_probs, key=cal_probs.get)
        confidence = cal_probs[top_cls]
        correct = 1.0 if row["actual_result"] == top_cls else 0.0
        errors.append((confidence, correct))
    df = pd.DataFrame(errors, columns=["confidence", "correct"])
    bins = np.linspace(0, 1, N_BINS + 1)
    bin_idx = np.clip(np.digitize(df["confidence"], bins) - 1, 0, N_BINS - 1)
    ece = 0.0
    n_total = len(df)
    for b in range(N_BINS):
        mask = bin_idx == b
        n = mask.sum()
        if n == 0:
            continue
        avg_conf = df.loc[mask, "confidence"].mean()
        avg_acc = df.loc[mask, "correct"].mean()
        ece += (n / n_total) * abs(avg_conf - avg_acc)
    return float(ece)


def main() -> None:
    if not BACKTEST_PATH.exists():
        raise FileNotFoundError(f"{BACKTEST_PATH} not found -- run src/evaluation/backtest.py first")
    backtest_df = pd.read_csv(BACKTEST_PATH)

    calibrators = fit_calibrators(backtest_df)
    method_used = "isotonic" if all(c is not None for c in calibrators.values()) else "raw_fallback_insufficient_samples"

    reliability_tables = pd.concat([_reliability_table(backtest_df, cls) for cls in CLASSES], ignore_index=True)
    OUT_RELIABILITY.parent.mkdir(parents=True, exist_ok=True)
    reliability_tables.to_csv(OUT_RELIABILITY, index=False)

    curve_rows = []
    for cls in CLASSES:
        cal = calibrators.get(cls)
        grid = np.linspace(0, 1, 21)
        calibrated_grid = cal.predict(grid) if cal is not None else grid
        for raw_p, cal_p in zip(grid, calibrated_grid):
            curve_rows.append({"outcome_class": cls, "raw_probability": round(float(raw_p), 3), "calibrated_probability": round(float(cal_p), 4)})
    pd.DataFrame(curve_rows).to_csv(OUT_CURVES, index=False)

    ece = expected_calibration_error(backtest_df, calibrators)
    raw_log_loss = backtest_df["dc_log_loss"].mean()

    calibrated_losses = []
    for _, row in backtest_df.iterrows():
        raw_probs = {cls: row[f"dc_{_col_suffix(cls)}"] for cls in CLASSES}
        cal_probs = apply_calibration(calibrators, raw_probs)
        p = max(cal_probs[row["actual_result"]], 1e-12)
        calibrated_losses.append(-np.log(p))
    calibrated_log_loss = float(np.mean(calibrated_losses))

    with open(OUT_REPORT, "w") as f:
        f.write("# EPL 2026-27 Calibration Report (Phase 1)\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(f"Calibration method: **{method_used}** (isotonic regression per outcome class, "
                f"fit on {len(backtest_df)} real backtest matches; minimum {MIN_SAMPLES_FOR_ISOTONIC} "
                f"samples required per class).\n\n")
        f.write("## Headline numbers\n\n")
        f.write(f"- Raw Dixon-Coles mean log loss: {raw_log_loss:.4f}\n")
        f.write(f"- Calibrated mean log loss: {calibrated_log_loss:.4f}\n")
        f.write(f"- Expected Calibration Error (top-class, 10 bins): {ece:.4f}\n\n")
        f.write("## Reliability tables\n\nSee `epl_2026_27_reliability_tables.csv` for the full per-bin breakdown "
                "(predicted probability vs. real empirical frequency) for each outcome class.\n\n")
        f.write("## Limitations\n\n"
                "- Backtest sample size (see above) is modest for 3-way isotonic calibration; bins with very "
                "few matches should be read with caution (see `n_matches` column in the reliability table).\n"
                "- Calibration is fit once on the full backtest window rather than with a separate held-out "
                "calibration fold, which can slightly overstate calibration quality; a proper train/calibrate/"
                "test split is a planned improvement.\n")
    print(f"Wrote calibration report ({method_used}, ECE={ece:.4f}) to {OUT_REPORT}")


if __name__ == "__main__":
    main()
