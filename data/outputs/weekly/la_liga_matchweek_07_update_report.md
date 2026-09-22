# LA_LIGA Matchweek 7 Update Report

Generated: 2026-09-22T10:26:09+00:00

Locked 10 real result(s). 311 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team               |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona       |                    0.05739 |                    0.00049 |                         0       |
| Atlético de Madrid |                    0.008   |                    0.06649 |                        -0.00011 |
| Rayo Vallecano     |                    1e-05   |                   -0.00588 |                        -0.00049 |
| Celta Vigo         |                    1e-05   |                    0.01773 |                        -0.05352 |
| Real Sociedad      |                    1e-05   |                    0.02514 |                        -0.0299  |
| Málaga CF          |                    0       |                   -0.00114 |                         0.05345 |
| Elche CF           |                    0       |                    0.00555 |                        -0.12582 |
| Getafe CF          |                    0       |                    0.00118 |                        -0.05378 |
| Valencia CF        |                    0       |                   -0.00393 |                         0.05695 |
| RC Deportivo       |                   -1e-05   |                   -0.0022  |                         0.01609 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9616 |  0.5677 | 0.184  |
| operational | dc_raw     |          10 |     0.9482 |  0.5603 | 0.1765 |
| operational | market     |           4 |     0.7482 |  0.4185 | 0.1273 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 15 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          15 |     0.8616 |  0.4989 | 0.1731 |
| operational | dc_raw     |          15 |     0.8334 |  0.4841 | 0.1653 |
| operational | market     |           5 |     0.7117 |  0.3915 | 0.1235 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                 | away_team        | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------------|:-----------------|:----------------|------------------------------------------:|
| RCD Espanyol de Barcelona | Elche CF         | away_win        |                                    0.2144 |
| RC Deportivo              | Real Betis       | draw            |                                    0.2879 |
| Athletic Club             | Deportivo Alavés | draw            |                                    0.2896 |
| CA Osasuna                | Rayo Vallecano   | draw            |                                    0.2986 |
| Valencia CF               | Real Sociedad    | away_win        |                                    0.328  |
| Atlético de Madrid        | Real Madrid      | home_win        |                                    0.3416 |
| Celta Vigo                | R. Racing Club   | home_win        |                                    0.4853 |
| Getafe CF                 | Málaga CF        | home_win        |                                    0.5235 |
| Villarreal CF             | Levante UD       | home_win        |                                    0.6242 |
| Sevilla FC                | FC Barcelona     | away_win        |                                    0.7028 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
