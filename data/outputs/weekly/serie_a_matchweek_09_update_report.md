# SERIE_A Matchweek 9 Update Report

Generated: 2026-10-30T11:45:04+00:00

Locked 10 real result(s). 290 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Lazio          |                    0.01576 |                    0.13855 |                        -3e-05   |
| Como           |                    0.01199 |                    0.07489 |                        -2e-05   |
| Roma           |                    0.00547 |                    0.02748 |                         0       |
| Napoli         |                    0.00223 |                    0.0686  |                        -0.00017 |
| Internazionale |                    0.00027 |                    0.00578 |                         0       |
| Bologna        |                    0.00016 |                    0.01503 |                        -0.0107  |
| Frosinone      |                    3e-05   |                    0.00057 |                        -0.0732  |
| Venezia        |                    0       |                    1e-05   |                        -0.0043  |
| Lecce          |                    0       |                   -0.00011 |                         0.11472 |
| Udinese        |                    0       |                   -0.00012 |                         0.01236 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9133 |  0.5243 | 0.1878 |
| operational | dc_raw     |          10 |     0.8414 |  0.4826 | 0.1688 |
| operational | market     |           6 |     0.9149 |  0.5241 | 0.1959 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 50 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          50 |     0.9358 |  0.5466 | 0.1942 |
| operational | dc_raw     |          50 |     0.9527 |  0.5542 | 0.1999 |
| operational | market     |          32 |     0.9936 |  0.5881 | 0.2308 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team   | away_team      | actual_result   |   predicted_probability_of_actual_outcome |
|:------------|:---------------|:----------------|------------------------------------------:|
| Genoa       | Juventus       | home_win        |                                    0.1792 |
| Milan       | Bologna        | away_win        |                                    0.1815 |
| Fiorentina  | Atalanta       | draw            |                                    0.2616 |
| Parma       | Udinese        | draw            |                                    0.301  |
| Sassuolo    | Lazio          | away_win        |                                    0.4808 |
| Frosinone   | Lecce          | home_win        |                                    0.5084 |
| Torino      | Como           | away_win        |                                    0.5402 |
| Monza       | Napoli         | away_win        |                                    0.5987 |
| Roma        | Cagliari       | home_win        |                                    0.6875 |
| Venezia     | Internazionale | away_win        |                                    0.7764 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
