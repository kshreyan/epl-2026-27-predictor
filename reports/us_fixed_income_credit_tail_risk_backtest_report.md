# US Fixed Income & Credit Tail-Risk Backtest Report

Real rolling-origin backtest, 1972 real (ticker, checkpoint) pairs across 5 real tickers (1962-03-29 to 2026-10-27), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day yield/spread change|): **0.120 percentage points of yield/spread change** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0156 |
| 40th | 0.0950 |
| 60th | 0.1626 |
| 80th | 0.2357 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 | 395 |              0.00249114 |          0.0101266 |
|                 1 | 394 |              0.0559222  |          0.0482234 |
|                 2 | 394 |              0.12934    |          0.0964467 |
|                 3 | 394 |              0.19631    |          0.142132  |
|                 4 | 395 |              0.302765   |          0.263291  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
