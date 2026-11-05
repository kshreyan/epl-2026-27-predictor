# US FX Tail-Risk Backtest Report

Real rolling-origin backtest, 406 real (ticker, checkpoint) pairs across 7 real tickers (2022-01-28 to 2026-10-05), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-trading-day return|): **0.9928%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0784 |
| 40th | 0.1427 |
| 60th | 0.1947 |
| 80th | 0.2442 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  82 |               0.0321921 |          0.0609756 |
|                 1 |  81 |               0.112386  |          0.0617284 |
|                 2 |  81 |               0.167801  |          0.0864198 |
|                 3 |  81 |               0.218704  |          0.160494  |
|                 4 |  81 |               0.287305  |          0.246914  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- A checkpoint every 21 real daily observation(s) is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
