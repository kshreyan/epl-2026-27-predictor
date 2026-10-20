# EPL Matchweek 7 Update Report

Generated: 2026-10-20T10:30:49+00:00

Locked 10 real result(s). 310 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal                |                    0.05193 |                    0.00773 |                         0       |
| Brighton & Hove Albion |                    0.01718 |                    0.105   |                        -0.00062 |
| Liverpool              |                    0.00384 |                    0.05714 |                        -0.00141 |
| Chelsea                |                    0.00359 |                    0.07198 |                        -0.00352 |
| Aston Villa            |                    0.00028 |                    0.01981 |                        -0.02456 |
| AFC Bournemouth        |                    8e-05   |                    0.00702 |                        -0.03628 |
| Tottenham Hotspur      |                    3e-05   |                    0.00089 |                        -0.07512 |
| Fulham                 |                    0       |                    0.00085 |                        -0.07103 |
| Ipswich Town           |                   -2e-05   |                   -0.00194 |                         0.01038 |
| Coventry City          |                   -2e-05   |                   -0.00156 |                         0.03124 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     0.7717 |   0.4383 |   0.1655 |
| operational | dc_raw     |          10 |     0.8004 |   0.4619 |   0.1753 |
| operational | market     |          10 |     0.7442 |   0.4135 |   0.1551 |
| preseason   | production |          10 |     0.7821 |   0.4471 |   0.1673 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 70 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          70 |     1.3564 |   0.5963 |   0.2    |
| operational | dc_raw     |          70 |     1.0559 |   0.6077 |   0.2082 |
| operational | market     |          70 |     1.0024 |   0.5995 |   0.1981 |
| preseason   | production |          70 |     1.0243 |   0.6104 |   0.2061 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team         | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:------------------|:----------------|------------------------------------------:|
| Leeds United           | Manchester United | draw            |                                    0.2594 |
| Newcastle United       | Aston Villa       | away_win        |                                    0.3251 |
| Brentford              | Liverpool         | away_win        |                                    0.3418 |
| Everton                | Chelsea           | away_win        |                                    0.3871 |
| AFC Bournemouth        | Sunderland        | home_win        |                                    0.4662 |
| Fulham                 | Hull City         | home_win        |                                    0.479  |
| Nottingham Forest      | Arsenal           | away_win        |                                    0.5607 |
| Brighton & Hove Albion | Crystal Palace    | home_win        |                                    0.594  |
| Tottenham Hotspur      | Coventry City     | home_win        |                                    0.6084 |
| Manchester City        | Ipswich Town      | home_win        |                                    0.8814 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
