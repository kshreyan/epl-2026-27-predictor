# EPL Matchweek 9 Update Report

Generated: 2026-11-04T13:22:19+00:00

Locked 10 real result(s). 290 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal                |                    0.13439 |                    0.00834 |                         0       |
| Brighton & Hove Albion |                    0.02079 |                    0.11976 |                        -0.00022 |
| Chelsea                |                    0.00226 |                    0.06296 |                        -0.003   |
| Brentford              |                    0.00107 |                    0.03098 |                        -0.00508 |
| AFC Bournemouth        |                    0.00066 |                    0.02505 |                        -0.01009 |
| Everton                |                    0.00015 |                    0.01199 |                        -0.03574 |
| Tottenham Hotspur      |                    4e-05   |                    0.00568 |                        -0.0439  |
| Ipswich Town           |                    0       |                   -0.00086 |                        -0.01194 |
| Coventry City          |                    0       |                    2e-05   |                        -0.08006 |
| Crystal Palace         |                   -1e-05   |                   -0.00214 |                         0.05696 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.0713 |   0.6455 |   0.2415 |
| operational | dc_raw     |          10 |     1.1161 |   0.68   |   0.2561 |
| operational | market     |          10 |     1.0068 |   0.6005 |   0.2209 |
| preseason   | production |          10 |     1.1228 |   0.6869 |   0.2607 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 90 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          90 |     1.2999 |   0.6123 |   0.2096 |
| operational | dc_raw     |          90 |     1.0685 |   0.6235 |   0.217  |
| operational | market     |          90 |     1.0184 |   0.6108 |   0.2063 |
| preseason   | production |          90 |     1.0476 |   0.6288 |   0.2157 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Manchester City   | Brighton & Hove Albion | away_win        |                                    0.1911 |
| Aston Villa       | Fulham                 | draw            |                                    0.2612 |
| Coventry City     | Sunderland             | home_win        |                                    0.2626 |
| Hull City         | Ipswich Town           | draw            |                                    0.267  |
| Newcastle United  | Everton                | away_win        |                                    0.2973 |
| Liverpool         | Arsenal                | away_win        |                                    0.4152 |
| AFC Bournemouth   | Leeds United           | home_win        |                                    0.4327 |
| Chelsea           | Manchester United      | home_win        |                                    0.4668 |
| Brentford         | Nottingham Forest      | home_win        |                                    0.4695 |
| Tottenham Hotspur | Crystal Palace         | home_win        |                                    0.543  |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
