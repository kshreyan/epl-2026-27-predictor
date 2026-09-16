# Model+Market Blend Backtest

Generated: 2026-09-16T20:11:53+00:00

Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats Dixon-Coles alone, using the exact same paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned -- an untuned 50/50 pool, tested once.

**Real historical market odds**: football-data.co.uk closing "Avg" columns (average across every bookmaker they track), 2142/2142 backtest matches matched (0 dropped, not estimated).

## Headline numbers

| | Dixon-Coles alone | Model+market blend |
|---|---|---|
| Log loss | 1.0026 | 0.9852 |
| Brier | 0.5976 | 0.5867 |
| RPS | 0.2056 | 0.2009 |

Paired bootstrap (10000 resamples): log-loss difference (DC - blend) point estimate **+0.0175** (positive favors the blend), 95% CI **[+0.0133, +0.0217]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        306       1.0005             0.9814                  True
2020-21        306       1.0156             0.9983                  True
2021-22        306       1.0107             0.9944                  True
2022-23        306       1.0062             0.9967                  True
2023-24        306       0.9761             0.9571                  True
2024-25        306       1.0313             1.0067                  True
2025-26        306       0.9781             0.9616                  True

Blend wins 7/7 seasons.

**The blend's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) -- promoted; live predictions use it for any fixture with real market odds available, falling back to model-only otherwise.**
