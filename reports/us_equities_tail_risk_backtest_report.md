# US Equities Tail-Risk Backtest Report

Real rolling-origin backtest, 1710 real (ticker, checkpoint) pairs across 30 real tickers (2022-02-02 to 2026-10-12), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-trading-day return|): **3.9697%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0596 |
| 40th | 0.1006 |
| 60th | 0.1444 |
| 80th | 0.1984 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 | 342 |               0.0342909 |          0.0292398 |
|                 1 | 342 |               0.0800652 |          0.0730994 |
|                 2 | 342 |               0.121153  |          0.0789474 |
|                 3 | 342 |               0.169474  |          0.143275  |
|                 4 | 342 |               0.255409  |          0.263158  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- A checkpoint every 21 real daily observation(s) is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
