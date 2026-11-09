# Model+Market Blend Backtest

Generated: 2026-11-09T09:46:01+00:00

Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats Dixon-Coles alone, using the exact same paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned -- an untuned 50/50 pool, tested once.

**Real historical market odds**: football-data.co.uk closing "Avg" columns (average across every bookmaker they track), 2337/2337 backtest matches matched (0 dropped, not estimated).

## Headline numbers

| | Dixon-Coles alone | Model+market blend |
|---|---|---|
| Log loss | 1.0108 | 0.9943 |
| Brier | 0.6040 | 0.5933 |
| RPS | 0.2095 | 0.2047 |

Paired bootstrap (10000 resamples): log-loss difference (DC - blend) point estimate **+0.0165** (positive favors the blend), 95% CI **[+0.0125, +0.0207]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        279       1.0064             0.9954                  True
2020-21        380       1.0301             1.0096                  True
2021-22        380       1.0136             1.0019                  True
2022-23        380       0.9920             0.9759                  True
2023-24        306       1.0364             1.0222                  True
2024-25        306       0.9849             0.9665                  True
2025-26        306       1.0111             0.9875                  True

Blend wins 7/7 seasons.

**The blend's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) -- promoted; live predictions use it for any fixture with real market odds available, falling back to model-only otherwise.**
