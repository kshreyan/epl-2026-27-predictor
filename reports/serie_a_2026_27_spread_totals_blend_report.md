# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest
Generated: 2026-09-16T19:05:18+00:00
Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned.

## Asian Handicap (spread)
**Real historical market odds**: football-data.co.uk closing averages, 2658/2660 backtest matches matched (2 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.7194 | 0.7007 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0187** (positive favors the blend), 95% CI **[+0.0147, +0.0229]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.7258             0.7056                  True
2020-21        379       0.7168             0.6992                  True
2021-22        379       0.7224             0.7017                  True
2022-23        380       0.7162             0.6989                  True
2023-24        380       0.7183             0.6990                  True
2024-25        380       0.7288             0.7049                  True
2025-26        380       0.7076             0.6957                  True

Blend wins 7/7 seasons.

**The Asian Handicap (spread) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**

## Over/Under 2.5 (totals)
**Real historical market odds**: football-data.co.uk closing averages, 2658/2660 backtest matches matched (2 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.6924 | 0.6838 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0087** (positive favors the blend), 95% CI **[+0.0057, +0.0117]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.6762             0.6677                  True
2020-21        379       0.6836             0.6784                  True
2021-22        379       0.7010             0.6877                  True
2022-23        380       0.7053             0.6907                  True
2023-24        380       0.6759             0.6759                 False
2024-25        380       0.7007             0.6874                  True
2025-26        380       0.7044             0.6986                  True

Blend wins 6/7 seasons.

**The Over/Under 2.5 (totals) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**
