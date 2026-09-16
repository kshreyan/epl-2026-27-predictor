# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest
Generated: 2026-09-16T07:16:26+00:00
Evaluates whether a 50/50 log-odds blend of the model's own probability and the real market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI must exclude zero AND win a season majority). No blend weight is tuned.

## Asian Handicap (spread)
**Real historical market odds**: football-data.co.uk closing averages, 2656/2660 backtest matches matched (4 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.7087 | 0.6968 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0119** (positive favors the blend), 95% CI **[+0.0088, +0.0152]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.7030             0.6938                  True
2020-21        380       0.7147             0.6989                  True
2021-22        380       0.7180             0.7007                  True
2022-23        380       0.7075             0.6950                  True
2023-24        380       0.7058             0.6961                  True
2024-25        380       0.7056             0.6960                  True
2025-26        376       0.7064             0.6969                  True

Blend wins 7/7 seasons.

**The Asian Handicap (spread) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**

## Over/Under 2.5 (totals)
**Real historical market odds**: football-data.co.uk closing averages, 2660/2660 backtest matches matched (0 dropped, not estimated).
| | Model-only | Model+market blend |
|---|---|---|
| Log loss | 0.6828 | 0.6739 |

Paired bootstrap (10000 resamples): log-loss difference (model - blend) point estimate **+0.0089** (positive favors the blend), 95% CI **[+0.0060, +0.0119]**.

 season  n_matches  dc_log_loss  ensemble_log_loss  ensemble_wins_season
2019-20        380       0.6814             0.6732                  True
2020-21        380       0.6926             0.6825                  True
2021-22        380       0.6924             0.6828                  True
2022-23        380       0.6912             0.6805                  True
2023-24        380       0.6634             0.6541                  True
2024-25        380       0.6738             0.6669                  True
2025-26        380       0.6850             0.6775                  True

Blend wins 7/7 seasons.

**The Over/Under 2.5 (totals) blend's edge is statistically significant -- promoted; live predictions use it for any fixture with a real market line/odds for this market, falling back to model-only otherwise.**
