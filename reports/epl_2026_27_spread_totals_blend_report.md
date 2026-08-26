# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest
Generated: 2026-08-25T22:40:14+00:00
Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned.

## Asian Handicap (spread)
**Real historical market odds**: football-data.co.uk closing averages, 2659/2660 backtest matches matched (1 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.7108 | 0.6969 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0138** (positive favors the blend), 95% CI **[+0.0101, +0.0176]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.6933             0.6869                  True
2020-21        380       0.7147             0.6979                  True
2021-22        380       0.7083             0.6947                  True
2022-23        380       0.7269             0.7041                  True
2023-24        380       0.7099             0.6973                  True
2024-25        380       0.7010             0.6924                  True
2025-26        379       0.7213             0.7054                  True

Blend wins 7/7 seasons.

**The Asian Handicap (spread) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**

## Over/Under 2.5 (totals)
**Real historical market odds**: football-data.co.uk closing averages, 2660/2660 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.6868 | 0.6775 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0093** (positive favors the blend), 95% CI **[+0.0062, +0.0126]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.6765             0.6680                  True
2020-21        380       0.7154             0.6990                  True
2021-22        380       0.6849             0.6802                  True
2022-23        380       0.6786             0.6711                  True
2023-24        380       0.6703             0.6559                  True
2024-25        380       0.6808             0.6773                  True
2025-26        380       0.7010             0.6909                  True

Blend wins 7/7 seasons.

**The Over/Under 2.5 (totals) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**
