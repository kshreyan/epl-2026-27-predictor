# US Commodities Tail-Risk Backtest Report

Real rolling-origin backtest, 684 real (ticker, checkpoint) pairs across 12 real tickers (2022-02-02 to 2026-10-09), EWMA (lambda=0.94) daily volatility scaled to a real 5-trading-day horizon, zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |5-trading-day return|): **4.5732%** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.0476 |
| 40th | 0.1006 |
| 60th | 0.1466 |
| 80th | 0.2158 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 | 137 |               0.0239655 |          0.0364964 |
|                 1 | 137 |               0.0763111 |          0.0291971 |
|                 2 | 136 |               0.123792  |          0.0882353 |
|                 3 | 137 |               0.174364  |          0.0948905 |
|                 4 | 137 |               0.291834  |          0.255474  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- A checkpoint every 21 real daily observation(s) is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
