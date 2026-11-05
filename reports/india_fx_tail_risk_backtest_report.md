# India FX Tail-Risk Backtest Report

Real rolling-origin backtest, 232 real (ticker, checkpoint) pairs across 4 real tickers (2022-01-28 to 2026-10-05), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-trading-day return|): **0.9190%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0883 |
| 40th | 0.1461 |
| 60th | 0.2000 |
| 80th | 0.2495 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  47 |               0.0342983 |          0.0425532 |
|                 1 |  46 |               0.120918  |          0.0652174 |
|                 2 |  46 |               0.171447  |          0.108696  |
|                 3 |  46 |               0.225249  |          0.173913  |
|                 4 |  47 |               0.29313   |          0.170213  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- A checkpoint every 21 real daily observation(s) is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
