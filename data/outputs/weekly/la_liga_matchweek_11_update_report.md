# LA_LIGA Matchweek 11 Update Report

Generated: 2026-11-04T13:23:00+00:00

Locked 10 real result(s). 280 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------------|---------------------------:|---------------------------:|--------------------------------:|
| Atlético de Madrid        |                    0.00444 |                    0.05094 |                        -1e-05   |
| Athletic Club             |                    4e-05   |                    0.03681 |                        -0.00466 |
| Elche CF                  |                    0       |                   -0.01492 |                         0.05383 |
| Levante UD                |                    0       |                   -0.00815 |                         0.05237 |
| R. Racing Club            |                    0       |                   -0.00034 |                         0.05384 |
| RC Deportivo              |                    0       |                    0.00128 |                        -0.0455  |
| Málaga CF                 |                    0       |                   -0.00014 |                         0.04699 |
| Valencia CF               |                    0       |                    0.00154 |                        -0.08284 |
| Getafe CF                 |                    0       |                    0.00246 |                        -0.08838 |
| RCD Espanyol de Barcelona |                    0       |                    0.00618 |                        -0.08815 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.8333 |  0.4711 | 0.2027 |
| operational | dc_raw     |          10 |     0.8214 |  0.4728 | 0.2082 |
| operational | market     |           4 |     0.9981 |  0.5964 | 0.2567 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 46 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          46 |     0.8953 |  0.5233 | 0.1841 |
| operational | dc_raw     |          46 |     0.8885 |  0.5236 | 0.1841 |
| operational | market     |          22 |     0.9384 |  0.555  | 0.1929 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team      | away_team                 | actual_result   |   predicted_probability_of_actual_outcome |
|:---------------|:--------------------------|:----------------|------------------------------------------:|
| Villarreal CF  | RCD Espanyol de Barcelona | away_win        |                                    0.1411 |
| Elche CF       | Valencia CF               | away_win        |                                    0.3188 |
| Getafe CF      | Sevilla FC                | home_win        |                                    0.3356 |
| Rayo Vallecano | Celta Vigo                | home_win        |                                    0.379  |
| Athletic Club  | Real Sociedad             | home_win        |                                    0.4446 |
| RC Deportivo   | CA Osasuna                | home_win        |                                    0.4698 |
| Levante UD     | Atlético de Madrid        | away_win        |                                    0.5487 |
| R. Racing Club | Real Madrid               | away_win        |                                    0.6644 |
| Real Betis     | Málaga CF                 | home_win        |                                    0.6835 |
| FC Barcelona   | Deportivo Alavés          | home_win        |                                    0.8077 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
