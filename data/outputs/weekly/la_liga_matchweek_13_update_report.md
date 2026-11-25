# LA_LIGA Matchweek 13 Update Report

Generated: 2026-11-25T19:58:47+00:00

Locked 10 real result(s). 251 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona              |                    0.00054 |                   -1e-05   |                         0       |
| Atlético de Madrid        |                    0.00022 |                   -0.00072 |                         0       |
| Real Betis                |                    9e-05   |                    0.00194 |                        -1e-05   |
| Real Sociedad             |                    1e-05   |                   -0.0004  |                         1e-05   |
| R. Racing Club            |                    0       |                   -8e-05   |                        -0.00115 |
| Athletic Club             |                    0       |                    0.00054 |                         0.00043 |
| Sevilla FC                |                    0       |                    0.00096 |                         7e-05   |
| Deportivo Alavés          |                    0       |                    0.00061 |                        -0.00056 |
| RCD Espanyol de Barcelona |                    0       |                    0.00025 |                        -0.00077 |
| Celta Vigo                |                    0       |                   -0.00037 |                        -0.00154 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9055 |  0.5256 | 0.1858 |
| operational | dc_raw     |          10 |     0.9683 |  0.571  | 0.2064 |
| operational | market     |           5 |     0.8951 |  0.5232 | 0.1458 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 75 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          75 |     0.8966 |  0.524  | 0.173  |
| operational | dc_raw     |          75 |     0.9131 |  0.5381 | 0.1779 |
| operational | market     |          38 |     0.8782 |  0.5125 | 0.161  |
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
| Levante UD       | Elche CF                  | draw            |                                    0.2896 |
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
