# UEL Model+Market Blend Report

**Genuinely thin -- read with real caution.** Only 2025-26 has a real collected ESPN closing line for this competition (see collect_espn_continental_cup_odds.py), so this backtest spans one real season and 54 real games, versus 2,660+ for a domestic league's own market-blend backtest. The 1-season breakdown below is real, not a typo -- there is only one.

## Model comparison (lower log loss is better)

| model | n_matches | log_loss | brier | rps |
|---|---:|---:|---:|---:|
| Model-only (Elo) | 54 | 0.9274 | 0.5431 | 0.1965 |
| Model + market blend | 54 | 0.8549 | 0.4923 | 0.1724 |

Paired bootstrap (10,000 resamples): point estimate +0.0725 (positive = blend better), 95% CI [+0.0374, +0.1056]. Season wins: blend beats model-only in 1/1 season(s).

**Blend significantly better than model-only: True**
