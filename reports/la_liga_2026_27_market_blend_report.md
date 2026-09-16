# Model+Market Blend Backtest

Generated: 2026-09-16T07:16:15+00:00

Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats Dixon-Coles alone, using the exact same paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned -- an untuned 50/50 pool, tested once.

**Real historical market odds**: football-data.co.uk closing "Avg" columns (average across every bookmaker they track), 2660/2660 backtest matches matched (0 dropped, not estimated).

## Headline numbers

| | Dixon-Coles alone | Model+market blend |
|---|---|---|
| Log loss | 0.9941 | 0.9791 |
| Brier | 0.5921 | 0.5826 |
| RPS | 0.1996 | 0.1953 |

Paired bootstrap (10000 resamples): log-loss difference (DC - blend) point estimate **+0.0151** (positive favors the blend), 95% CI **[+0.0116, +0.0189]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       1.0026             0.9884                  True
2020-21        380       1.0178             0.9972                  True
2021-22        380       1.0090             0.9943                  True
2022-23        380       1.0065             0.9896                  True
2023-24        380       0.9637             0.9526                  True
2024-25        380       0.9722             0.9595                  True
2025-26        380       0.9872             0.9719                  True

Blend wins 7/7 seasons.

**The blend's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) -- promoted; live predictions use it for any fixture with real market odds available, falling back to model-only otherwise.**
