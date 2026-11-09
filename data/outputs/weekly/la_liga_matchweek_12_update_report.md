# LA_LIGA Matchweek 12 Update Report

Generated: 2026-11-09T14:31:20+00:00

Locked 10 real result(s). 261 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team             |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona     |                    0.0336  |                    0.00013 |                         0       |
| Real Betis       |                    0.00012 |                    0.09852 |                        -0.00013 |
| Villarreal CF    |                    1e-05   |                    0.00481 |                        -0.00309 |
| Sevilla FC       |                    0       |                   -0.01981 |                         0.00023 |
| CA Osasuna       |                    0       |                   -0.0008  |                        -0.00849 |
| RC Deportivo     |                    0       |                   -0.00081 |                        -0.02924 |
| Rayo Vallecano   |                    0       |                   -0.01003 |                         0.01044 |
| Celta Vigo       |                    0       |                   -0.0086  |                         0.00469 |
| Elche CF         |                    0       |                   -0.00776 |                         0.046   |
| Deportivo Alavés |                    0       |                   -0.0029  |                        -0.01396 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9836 |  0.5915 | 0.1727 |
| operational | dc_raw     |          10 |     0.9802 |  0.5847 | 0.1686 |
| operational | market     |           6 |     0.7977 |  0.4544 | 0.1212 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 65 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          65 |     0.8953 |  0.5237 | 0.171  |
| operational | dc_raw     |          65 |     0.9046 |  0.533  | 0.1735 |
| operational | market     |          33 |     0.8757 |  0.5109 | 0.1633 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                 | away_team        | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------------|:-----------------|:----------------|------------------------------------------:|
| Málaga CF                 | R. Racing Club   | away_win        |                                    0.2395 |
| Celta Vigo                | Levante UD       | draw            |                                    0.2544 |
| Sevilla FC                | Deportivo Alavés | draw            |                                    0.2816 |
| RCD Espanyol de Barcelona | RC Deportivo     | draw            |                                    0.2849 |
| CA Osasuna                | Athletic Club    | draw            |                                    0.3006 |
| Atlético de Madrid        | FC Barcelona     | away_win        |                                    0.3974 |
| Elche CF                  | Real Betis       | away_win        |                                    0.4242 |
| Real Sociedad             | Rayo Vallecano   | home_win        |                                    0.5296 |
| Villarreal CF             | Getafe CF        | home_win        |                                    0.6208 |
| Valencia CF               | Real Madrid      | away_win        |                                    0.6568 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
