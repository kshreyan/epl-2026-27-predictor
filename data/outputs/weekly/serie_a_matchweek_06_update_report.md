# SERIE_A Matchweek 6 Update Report

Generated: 2026-10-13T13:02:44+00:00

Locked 10 real result(s). 320 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Internazionale |                    0.056   |                    0.01167 |                         0       |
| Napoli         |                    0.0096  |                    0.08246 |                        -0.00021 |
| Lazio          |                    0.00193 |                    0.03325 |                        -0.00047 |
| Atalanta       |                    0.00108 |                    0.01807 |                        -0.00054 |
| Bologna        |                    8e-05   |                    0.00478 |                        -0.01904 |
| Torino         |                    1e-05   |                    0.00171 |                        -0.05694 |
| Genoa          |                    0       |                    0.00039 |                        -0.09368 |
| Lecce          |                    0       |                   -5e-05   |                         0.03268 |
| Venezia        |                    0       |                   -6e-05   |                         0.03135 |
| Monza          |                    0       |                   -0.00018 |                         0.03661 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.8597 |  0.502  | 0.1462 |
| operational | dc_raw     |          10 |     0.8199 |  0.475  | 0.1376 |
| operational | market     |           6 |     0.8823 |  0.5225 | 0.1833 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 20 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          20 |     0.9948 |  0.5915 | 0.1903 |
| operational | dc_raw     |          20 |     1.0049 |  0.5996 | 0.1975 |
| operational | market     |          13 |     1.0824 |  0.6566 | 0.2373 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team      | away_team   | actual_result   |   predicted_probability_of_actual_outcome |
|:---------------|:------------|:----------------|------------------------------------------:|
| Cagliari       | Juventus    | draw            |                                    0.2264 |
| Sassuolo       | Milan       | draw            |                                    0.2466 |
| Como           | Roma        | draw            |                                    0.2957 |
| Genoa          | Fiorentina  | home_win        |                                    0.3102 |
| Torino         | Udinese     | home_win        |                                    0.3989 |
| Lecce          | Bologna     | away_win        |                                    0.4606 |
| Lazio          | Monza       | home_win        |                                    0.6035 |
| Napoli         | Frosinone   | home_win        |                                    0.6339 |
| Atalanta       | Venezia     | home_win        |                                    0.6915 |
| Internazionale | Parma       | home_win        |                                    0.7417 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
