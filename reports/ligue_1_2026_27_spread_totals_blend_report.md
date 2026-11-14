# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest
Generated: 2026-11-14T10:44:27+00:00
Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned.

## Asian Handicap (spread)
**Real historical market odds**: football-data.co.uk closing averages, 2337/2337 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.7100 | 0.6971 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0129** (positive favors the blend), 95% CI **[+0.0093, +0.0166]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        279       0.7120             0.6998                  True
2020-21        380       0.7163             0.6992                  True
2021-22        380       0.6990             0.6902                  True
2022-23        380       0.7009             0.6901                  True
2023-24        306       0.7099             0.6994                  True
2024-25        306       0.7137             0.6983                  True
2025-26        306       0.7218             0.7057                  True

Blend wins 7/7 seasons.

**The Asian Handicap (spread) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**

## Over/Under 2.5 (totals)
**Real historical market odds**: football-data.co.uk closing averages, 2337/2337 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.6927 | 0.6814 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0113** (positive favors the blend), 95% CI **[+0.0080, +0.0148]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        279       0.6919             0.6763                  True
2020-21        380       0.7019             0.6885                  True
2021-22        380       0.6983             0.6861                  True
2022-23        380       0.6892             0.6787                  True
2023-24        306       0.6918             0.6859                  True
2024-25        306       0.6808             0.6731                  True
2025-26        306       0.6924             0.6789                  True

Blend wins 7/7 seasons.

**The Over/Under 2.5 (totals) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**
