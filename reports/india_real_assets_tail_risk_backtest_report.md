# India Real Assets Tail-Risk Backtest Report

Real rolling-origin backtest, 206 real (ticker, checkpoint) pairs across 4 real tickers (2022-02-02 to 2026-10-09), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day return|): **1.8188%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.1542 |
| 40th | 0.1975 |
| 60th | 0.2239 |
| 80th | 0.2573 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  42 |                0.114664 |          0.0952381 |
|                 1 |  41 |                0.17472  |          0.0487805 |
|                 2 |  41 |                0.210758 |          0.097561  |
|                 3 |  41 |                0.238868 |          0.121951  |
|                 4 |  41 |                0.290367 |          0.121951  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
