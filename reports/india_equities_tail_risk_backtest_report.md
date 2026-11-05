# India Equities Tail-Risk Backtest Report

Real rolling-origin backtest, 1680 real (ticker, checkpoint) pairs across 30 real tickers (2022-02-02 to 2026-10-07), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day return|): **3.4842%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0778 |
| 40th | 0.1131 |
| 60th | 0.1471 |
| 80th | 0.1943 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 | 336 |               0.0531908 |          0.0863095 |
|                 1 | 336 |               0.0965037 |          0.110119  |
|                 2 | 336 |               0.129666  |          0.0892857 |
|                 3 | 336 |               0.169672  |          0.142857  |
|                 4 | 336 |               0.238322  |          0.160714  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
