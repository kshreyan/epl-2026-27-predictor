# MLS 2026-27 Calibration Report (Phase 1)

Generated: 2026-09-21T06:15:34+00:00

Calibration method: **isotonic** (isotonic regression per outcome class, fit on 1481 real backtest matches; minimum 500 samples required per class).

## Headline numbers

- Raw Dixon-Coles mean log loss: 1.0848
- Calibrated mean log loss: 1.0446
- Expected Calibration Error (top-class, 10 bins): 0.0142

## Reliability tables

See `mls_2026_27_reliability_tables.csv` for the full per-bin breakdown (predicted probability vs. real empirical frequency) for each outcome class.

## Limitations

- Backtest sample size (see above) is modest for 3-way isotonic calibration; bins with very few matches should be read with caution (see `n_matches` column in the reliability table).
- Calibration is fit once on the full backtest window rather than with a separate held-out calibration fold, which can slightly overstate calibration quality; a proper train/calibrate/test split is a planned improvement.
