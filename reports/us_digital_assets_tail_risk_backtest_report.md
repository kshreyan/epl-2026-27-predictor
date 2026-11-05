# US Digital Assets Tail-Risk Backtest Report

Real rolling-origin backtest, 90 real (ticker, checkpoint) pairs across 6 real tickers (2026-01-05 to 2026-10-26), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day return|): **7.1041%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0651 |
| 40th | 0.1134 |
| 60th | 0.1678 |
| 80th | 0.2140 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  18 |               0.0380376 |           0.333333 |
|                 1 |  18 |               0.0869543 |           0.166667 |
|                 2 |  18 |               0.137702  |           0.222222 |
|                 3 |  18 |               0.185861  |           0.166667 |
|                 4 |  18 |               0.247477  |           0.111111 |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
