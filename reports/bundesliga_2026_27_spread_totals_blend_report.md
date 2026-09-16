# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest
Generated: 2026-09-16T20:11:55+00:00
Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned.

## Asian Handicap (spread)
**Real historical market odds**: football-data.co.uk closing averages, 2142/2142 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.7148 | 0.6999 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0149** (positive favors the blend), 95% CI **[+0.0111, +0.0189]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        306       0.7125             0.6980                  True
2020-21        306       0.7213             0.7036                  True
2021-22        306       0.7136             0.6988                  True
2022-23        306       0.7085             0.6968                  True
2023-24        306       0.7213             0.7029                  True
2024-25        306       0.7151             0.6982                  True
2025-26        306       0.7115             0.7008                  True

Blend wins 7/7 seasons.

**The Asian Handicap (spread) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**

## Over/Under 2.5 (totals)
**Real historical market odds**: football-data.co.uk closing averages, 2142/2142 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.6615 | 0.6517 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0098** (positive favors the blend), 95% CI **[+0.0063, +0.0134]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        306       0.6559             0.6454                  True
2020-21        306       0.6580             0.6502                  True
2021-22        306       0.6601             0.6507                  True
2022-23        306       0.6835             0.6750                  True
2023-24        306       0.6568             0.6465                  True
2024-25        306       0.6526             0.6460                  True
2025-26        306       0.6639             0.6483                  True

Blend wins 7/7 seasons.

**The Over/Under 2.5 (totals) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**
