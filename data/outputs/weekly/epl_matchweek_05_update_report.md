# EPL Matchweek 5 Update Report

Generated: 2026-09-21T07:34:02+00:00

Locked 10 real result(s). 330 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Manchester City        |                    0.121   |                    0.00725 |                         0       |
| Liverpool              |                    0.01703 |                    0.07426 |                        -0.00152 |
| Brighton & Hove Albion |                    0.01544 |                    0.1526  |                        -0.00563 |
| Brentford              |                    0.0047  |                    0.06727 |                        -0.00998 |
| Newcastle United       |                    0.0019  |                    0.01787 |                        -0.00793 |
| Aston Villa            |                    0.00065 |                    0.01358 |                        -0.02622 |
| Everton                |                    0.00034 |                    0.00263 |                        -0.01378 |
| Crystal Palace         |                    2e-05   |                   -0.00185 |                        -0.01373 |
| Tottenham Hotspur      |                   -3e-05   |                   -0.00517 |                         0.04409 |
| Fulham                 |                   -4e-05   |                   -0.00416 |                        -0.0032  |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     3.648  |   0.6949 |   0.2698 |
| operational | dc_raw     |          10 |     1.355  |   0.6951 |   0.2699 |
| operational | market     |          10 |     1.0601 |   0.6362 |   0.2406 |
| preseason   | production |          10 |     1.0017 |   0.589  |   0.217  |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 50 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          50 |     1.5254 |   0.6146 |   0.2006 |
| operational | dc_raw     |          50 |     1.0632 |   0.6121 |   0.2029 |
| operational | market     |          50 |     1.051  |   0.634  |   0.206  |
| preseason   | production |          50 |     1.0482 |   0.6265 |   0.2065 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team         | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:------------------|:----------------|------------------------------------------:|
| Nottingham Forest      | Coventry City     | away_win        |                                    0      |
| Brighton & Hove Albion | Arsenal           | home_win        |                                    0.2107 |
| Leeds United           | Crystal Palace    | draw            |                                    0.2581 |
| Fulham                 | Manchester United | draw            |                                    0.2614 |
| Tottenham Hotspur      | Aston Villa       | away_win        |                                    0.3207 |
| Brentford              | Chelsea           | home_win        |                                    0.3671 |
| AFC Bournemouth        | Liverpool         | away_win        |                                    0.4165 |
| Newcastle United       | Hull City         | home_win        |                                    0.4927 |
| Everton                | Ipswich Town      | home_win        |                                    0.6136 |
| Manchester City        | Sunderland        | home_win        |                                    0.681  |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
