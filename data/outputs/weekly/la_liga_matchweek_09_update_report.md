# LA_LIGA Matchweek 9 Update Report

Generated: 2026-10-20T10:31:29+00:00

Locked 10 real result(s). 301 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona              |                    0.02326 |                    0.00051 |                         0       |
| Real Sociedad             |                    9e-05   |                    0.05762 |                        -0.01689 |
| Celta Vigo                |                    0       |                    0.01759 |                        -0.01946 |
| R. Racing Club            |                    0       |                   -0.00175 |                         0.03609 |
| Málaga CF                 |                    0       |                   -0.00071 |                         0.04794 |
| Elche CF                  |                    0       |                    0.00344 |                        -0.03592 |
| CA Osasuna                |                    0       |                    0.00503 |                        -0.05224 |
| Valencia CF               |                    0       |                   -0.00053 |                         0.00458 |
| Getafe CF                 |                    0       |                   -0.00081 |                         0.00676 |
| RCD Espanyol de Barcelona |                    0       |                   -0.0026  |                         0.0204  |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.8945 |  0.5277 | 0.1393 |
| operational | dc_raw     |          10 |     0.8617 |  0.4981 | 0.1252 |
| operational | market     |           5 |     0.9582 |  0.5767 | 0.118  |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 25 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          25 |     0.8748 |  0.5104 | 0.1596 |
| operational | dc_raw     |          25 |     0.8447 |  0.4897 | 0.1492 |
| operational | market     |          10 |     0.835  |  0.4841 | 0.1207 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                 | away_team          | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------------|:-------------------|:----------------|------------------------------------------:|
| Villarreal CF             | Elche CF           | draw            |                                    0.1956 |
| RC Deportivo              | Levante UD         | draw            |                                    0.2777 |
| Valencia CF               | Athletic Club      | draw            |                                    0.301  |
| Getafe CF                 | Rayo Vallecano     | draw            |                                    0.3235 |
| Málaga CF                 | Real Sociedad      | away_win        |                                    0.3493 |
| Celta Vigo                | Deportivo Alavés   | home_win        |                                    0.5031 |
| RCD Espanyol de Barcelona | Atlético de Madrid | away_win        |                                    0.5166 |
| CA Osasuna                | R. Racing Club     | home_win        |                                    0.5906 |
| Real Betis                | FC Barcelona       | away_win        |                                    0.6138 |
| Real Madrid               | Sevilla FC         | home_win        |                                    0.7487 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
