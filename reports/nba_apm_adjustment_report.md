# NBA Box-Score APM Adjustment Signal Report

Generated: 2026-10-28T20:24:31+00:00

Real within-season test (2025-26): real player ratings fit via Ridge regression on the real earlier portion of the season (by date), tested against the real later portion, on top of Elo-only (this league's own real moneyline backtest winner). Run on 2 real, different split points -- a single-slice bootstrap CI that happens to exclude zero is exactly the kind of fragile, noise-driven finding this project's own recalibration_gate.py requires confirmation on multiple real slices to guard against; both splits must independently show a real significant edge before this signal is wired into live predictions, never acted on from one slice alone.

**Real, disclosed scope limitation**: game-level, not true stint-level RAPM -- see nba_apm_model.py's module docstring.

| train_fraction | split date | n | coefficient | 95% CI | significant |
|---|---|---|---|---|---|
| 0.7 | 2026-02-25 | 370 | 24.4250 | [+0.0108, +52.7156] | True |
| 0.8 | 2026-03-12 | 247 | 24.9466 | [-11.2353, +60.6786] | False |

## Verdict

**Not confirmed across real slices.** At least one real split's bootstrap CI includes zero -- the real finding does not replicate consistently, so the APM adjustment is NOT wired into live predictions; Elo-only remains primary. A real, honest result: a single real season's box-score data is a modest sample for this signal (the coefficient's real sign was positive on both slices tested, but significance was not robust to the exact split point), and multiple real seasons of real box-score data is the most likely path to a confirmed result later, not assumed to arrive automatically.
