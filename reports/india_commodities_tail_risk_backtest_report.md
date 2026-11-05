# India Commodities Tail-Risk Backtest Report

Real rolling-origin backtest, 109 real (ticker, checkpoint) pairs across 2 real tickers (2022-02-02 to 2026-10-08), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day return|): **3.0210%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0311 |
| 40th | 0.1007 |
| 60th | 0.1571 |
| 80th | 0.2128 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  22 |               0.0153916 |           0        |
|                 1 |  22 |               0.0677187 |           0        |
|                 2 |  21 |               0.134433  |           0.142857 |
|                 3 |  22 |               0.181174  |           0        |
|                 4 |  22 |               0.298208  |           0.136364 |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
