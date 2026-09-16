# Model+Market Blend Backtest

Generated: 2026-09-16T19:05:08+00:00

Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats Dixon-Coles alone, using the exact same paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned -- an untuned 50/50 pool, tested once.

**Real historical market odds**: football-data.co.uk closing "Avg" columns (average across every bookmaker they track), 2659/2660 backtest matches matched (1 dropped, not estimated).

## Headline numbers

| | Dixon-Coles alone | Model+market blend |
|---|---|---|
| Log loss | 0.9926 | 0.9727 |
| Brier | 0.5908 | 0.5787 |
| RPS | 0.1991 | 0.1936 |

Paired bootstrap (10000 resamples): log-loss difference (DC - blend) point estimate **+0.0199** (positive favors the blend), 95% CI **[+0.0153, +0.0247]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       1.0004             0.9750                  True
2020-21        380       0.9586             0.9409                  True
2021-22        379       1.0055             0.9842                  True
2022-23        380       1.0027             0.9851                  True
2023-24        380       0.9994             0.9782                  True
2024-25        380       0.9860             0.9621                  True
2025-26        380       0.9956             0.9835                  True

Blend wins 7/7 seasons.

**The blend's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) -- promoted; live predictions use it for any fixture with real market odds available, falling back to model-only otherwise.**
