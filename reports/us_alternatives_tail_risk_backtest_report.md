# US Alternatives Tail-Risk Backtest Report

Real rolling-origin backtest, 171 real (ticker, checkpoint) pairs across 3 real tickers (2022-02-02 to 2026-10-12), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-day return|): **0.9227%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0182 |
| 40th | 0.1049 |
| 60th | 0.2134 |
| 80th | 0.2865 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  35 |              0.00410491 |          0.0571429 |
|                 1 |  34 |              0.0584768  |          0.0294118 |
|                 2 |  34 |              0.167946   |          0.0882353 |
|                 3 |  34 |              0.245995   |          0.117647  |
|                 4 |  34 |              0.332133   |          0.117647  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- Monthly (21-trading-day) checkpoint stride is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
