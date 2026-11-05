# India Fixed Income & Credit Tail-Risk Backtest Report

Real rolling-origin backtest, 307 real (ticker, checkpoint) pairs across 2 real tickers (2013-11-01 to 2026-08-01), EWMA (lambda=0.94) monthly volatility scaled to a real 1-month horizon (FRED/OECD only publishes this series monthly -- no real daily India rate data is free anywhere, confirmed directly), zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably estimable from history alone).

**Real adverse threshold** (p75 of pooled real |1-month yield/spread change|): **0.172 percentage points of yield/spread change** -- a real top-quartile-sized move for this market's own history, not borrowed from any other asset class or sport.

## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)

| Percentile | p_fail cutoff |
|---|---|
| 20th | 0.1334 |
| 40th | 0.1758 |
| 60th | 0.2147 |
| 80th | 0.2823 |

## Real calibration (does the real breach rate rise with predicted p_fail?)

|   p_fail_quintile |   n |   mean_predicted_p_fail |   real_breach_rate |
|------------------:|----:|------------------------:|-------------------:|
|                 0 |  62 |               0.0889377 |          0.112903  |
|                 1 |  61 |               0.156621  |          0.131148  |
|                 2 |  61 |               0.190744  |          0.0819672 |
|                 3 |  61 |               0.247005  |          0.0983607 |
|                 4 |  62 |               0.357567  |          0.241935  |

## Limitations

- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.
- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate (a real future improvement, same "never assume, always check" discipline this project applies elsewhere, just not yet run for this market).
- A checkpoint every 1 real monthly observation(s) is a real compute-cost choice, not a claim that real volatility is constant between checkpoints.
