# LA_LIGA Matchweek 10 Update Report

Generated: 2026-10-27T11:09:35+00:00

Locked 10 real result(s). 290 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team               |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------|---------------------------:|---------------------------:|--------------------------------:|
| Real Madrid        |                    0.10156 |                    0.01301 |                         0       |
| Atlético de Madrid |                    0.01263 |                    0.00673 |                         0       |
| Villarreal CF      |                    0.00023 |                    0.04464 |                        -0.00351 |
| Real Sociedad      |                    9e-05   |                    0.01445 |                        -0.00668 |
| Athletic Club      |                    4e-05   |                    0.03447 |                        -0.02488 |
| Sevilla FC         |                    3e-05   |                    0.01464 |                        -0.01869 |
| Valencia CF        |                    0       |                   -0.00184 |                         0.03811 |
| RC Deportivo       |                    0       |                   -0.00144 |                        -0.0172  |
| Levante UD         |                    0       |                   -0.01359 |                         0.00639 |
| Rayo Vallecano     |                    0       |                   -0.02039 |                         0.05853 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9775 |  0.5857 | 0.2128 |
| operational | dc_raw     |          10 |     1.057  |  0.6539 | 0.2406 |
| operational | market     |           7 |     0.9984 |  0.5957 | 0.2349 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 36 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          36 |     0.9126 |  0.5378 | 0.179  |
| operational | dc_raw     |          36 |     0.9071 |  0.5378 | 0.1774 |
| operational | market     |          18 |     0.9251 |  0.5458 | 0.1787 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team          | away_team                 | actual_result   |   predicted_probability_of_actual_outcome |
|:-------------------|:--------------------------|:----------------|------------------------------------------:|
| Rayo Vallecano     | Elche CF                  | away_win        |                                    0.2134 |
| FC Barcelona       | Real Madrid               | away_win        |                                    0.218  |
| Deportivo Alavés   | Málaga CF                 | draw            |                                    0.2403 |
| Celta Vigo         | Real Betis                | draw            |                                    0.2881 |
| R. Racing Club     | RCD Espanyol de Barcelona | home_win        |                                    0.3962 |
| Valencia CF        | Villarreal CF             | away_win        |                                    0.4163 |
| Sevilla FC         | CA Osasuna                | home_win        |                                    0.5006 |
| Athletic Club      | Getafe CF                 | home_win        |                                    0.5192 |
| Real Sociedad      | Levante UD                | home_win        |                                    0.5483 |
| Atlético de Madrid | RC Deportivo              | home_win        |                                    0.7513 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
