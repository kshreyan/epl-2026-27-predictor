# LA_LIGA Matchweek 8 Update Report

Generated: 2026-11-09T06:08:30+00:00

Locked 9 real result(s). 271 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------------|---------------------------:|---------------------------:|--------------------------------:|
| Atlético de Madrid        |                    0.00301 |                    0.01209 |                         0       |
| Real Betis                |                    8e-05   |                    0.0804  |                        -0.00037 |
| Elche CF                  |                    0       |                   -0.0072  |                         0.00081 |
| Deportivo Alavés          |                    0       |                   -0.00646 |                         0.01072 |
| R. Racing Club            |                    0       |                   -0.001   |                        -0.00497 |
| RC Deportivo              |                    0       |                   -0.00157 |                         0.00596 |
| Valencia CF               |                    0       |                   -0.00106 |                        -0.01212 |
| Getafe CF                 |                    0       |                   -0.00172 |                         0.00594 |
| CA Osasuna                |                    0       |                   -0.00282 |                         0.035   |
| RCD Espanyol de Barcelona |                    0       |                   -0.00392 |                        -0.00583 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.7969 |  0.4508 | 0.1023 |
| operational | dc_raw     |           9 |     0.9028 |  0.5237 | 0.1249 |
| operational | market     |           5 |     0.6932 |  0.3848 | 0.0834 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 55 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          55 |     0.8792 |  0.5114 | 0.1707 |
| operational | dc_raw     |          55 |     0.8908 |  0.5237 | 0.1744 |
| operational | market     |          27 |     0.893  |  0.5235 | 0.1726 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team        | away_team                 | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------|:--------------------------|:----------------|------------------------------------------:|
| R. Racing Club   | Valencia CF               | draw            |                                    0.2654 |
| Levante UD       | Sevilla FC                | draw            |                                    0.2925 |
| Elche CF         | Celta Vigo                | draw            |                                    0.2985 |
| Málaga CF        | RCD Espanyol de Barcelona | draw            |                                    0.335  |
| Deportivo Alavés | Atlético de Madrid        | away_win        |                                    0.4958 |
| Real Betis       | CA Osasuna                | home_win        |                                    0.5785 |
| Real Sociedad    | RC Deportivo              | home_win        |                                    0.59   |
| Real Madrid      | Villarreal CF             | home_win        |                                    0.69   |
| FC Barcelona     | Getafe CF                 | home_win        |                                    0.8466 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
