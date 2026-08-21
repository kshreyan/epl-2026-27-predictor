# Model+Market Blend Backtest

Generated: 2026-08-21T04:13:57+00:00

Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats Dixon-Coles alone, using the exact same paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned -- an untuned 50/50 pool, tested once.

**Real historical market odds**: football-data.co.uk closing "Avg" columns (average across every bookmaker they track), 2660/2660 backtest matches matched (0 dropped, not estimated).

## Headline numbers

| | Dixon-Coles alone | Model+market blend |
|---|---|---|
| Log loss | 0.9865 | 0.9717 |
| Brier | 0.5864 | 0.5772 |
| RPS | 0.2035 | 0.1993 |

Paired bootstrap (10000 resamples): log-loss difference (DC - blend) point estimate **+0.0148** (positive favors the blend), 95% CI **[+0.0106, +0.0192]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.9716             0.9673                  True
2020-21        380       1.0275             1.0096                  True
2021-22        380       0.9538             0.9382                  True
2022-23        380       1.0192             0.9873                  True
2023-24        380       0.9198             0.9096                  True
2024-25        380       0.9706             0.9658                  True
2025-26        380       1.0433             1.0242                  True

Blend wins 7/7 seasons.

**The blend's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) -- promoted; live predictions use it for any fixture with real market odds available, falling back to model-only otherwise.**
