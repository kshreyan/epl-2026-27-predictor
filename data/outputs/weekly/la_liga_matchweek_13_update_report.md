# LA_LIGA Matchweek 13 Update Report

Generated: 2026-11-23T16:38:36+00:00

Locked 9 real result(s). 252 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team               |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------|---------------------------:|---------------------------:|--------------------------------:|
| Atlético de Madrid |                    0.00669 |                    0.03212 |                         0       |
| Real Madrid        |                    0.00035 |                    0.00122 |                         0       |
| Deportivo Alavés   |                    0       |                    0.00479 |                        -0.03932 |
| Sevilla FC         |                    0       |                   -0.00186 |                         0.00125 |
| Valencia CF        |                    0       |                    0.001   |                        -0.09281 |
| RC Deportivo       |                    0       |                   -0.00036 |                         0.05617 |
| Rayo Vallecano     |                    0       |                   -0.00424 |                         0.05428 |
| Celta Vigo         |                    0       |                    0.00054 |                         0.00785 |
| Levante UD         |                    0       |                    0.00117 |                         0.01081 |
| CA Osasuna         |                    0       |                    0.00036 |                        -0.04134 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.8685 |  0.4979 | 0.1915 |
| operational | dc_raw     |           9 |     0.9214 |  0.5383 | 0.2126 |
| operational | market     |           4 |     0.7882 |  0.4497 | 0.1475 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 74 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          74 |     0.892  |  0.5206 | 0.1735 |
| operational | dc_raw     |          74 |     0.9066 |  0.5337 | 0.1783 |
| operational | market     |          37 |     0.8662 |  0.5043 | 0.1616 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team        | away_team                 | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------|:--------------------------|:----------------|------------------------------------------:|
| Athletic Club    | RCD Espanyol de Barcelona | away_win        |                                    0.1998 |
| Rayo Vallecano   | Valencia CF               | away_win        |                                    0.283  |
| Sevilla FC       | Real Betis                | draw            |                                    0.3031 |
| R. Racing Club   | Real Sociedad             | home_win        |                                    0.3198 |
| Getafe CF        | Atlético de Madrid        | away_win        |                                    0.4813 |
| Deportivo Alavés | RC Deportivo              | home_win        |                                    0.5015 |
| CA Osasuna       | Málaga CF                 | home_win        |                                    0.5707 |
| FC Barcelona     | Villarreal CF             | home_win        |                                    0.7194 |
| Real Madrid      | Celta Vigo                | home_win        |                                    0.7423 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
