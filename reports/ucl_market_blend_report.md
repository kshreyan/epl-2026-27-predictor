# UCL Model+Market Blend Report

**Genuinely thin -- read with real caution.** Only 2025-26 has a real collected ESPN closing line for this competition (see collect_espn_continental_cup_odds.py), so this backtest spans one real season and 54 real games, versus 2,660+ for a domestic league's own market-blend backtest. The 1-season breakdown below is real, not a typo -- there is only one.

## Model comparison (lower log loss is better)

| model | n_matches | log_loss | brier | rps |
|---|---:|---:|---:|---:|
| Model-only (Dixon-Coles) | 54 | 0.9527 | 0.5554 | 0.2171 |
| Model + market blend | 54 | 0.9180 | 0.5437 | 0.2125 |

Paired bootstrap (10,000 resamples): point estimate +0.0348 (positive = blend better), 95% CI [-0.0274, +0.1063]. Season wins: blend beats model-only in 1/1 season(s).

**Blend significantly better than model-only: False**
