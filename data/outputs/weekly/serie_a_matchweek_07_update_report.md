# SERIE_A Matchweek 7 Update Report

Generated: 2026-10-20T10:32:19+00:00

Locked 10 real result(s). 310 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Internazionale |                    0.02443 |                    0.01347 |                         0       |
| Lazio          |                    0.01225 |                    0.15997 |                        -0.00035 |
| Roma           |                    0.01026 |                    0.04722 |                         0       |
| Milan          |                    0.00534 |                    0.09346 |                        -0.00011 |
| Como           |                    0.00487 |                    0.0862  |                        -4e-05   |
| Torino         |                    8e-05   |                    0.00461 |                        -0.03061 |
| Frosinone      |                    2e-05   |                    0.00057 |                        -0.0867  |
| Venezia        |                    0       |                    5e-05   |                        -0.0819  |
| Genoa          |                    0       |                   -0.00038 |                         0.05504 |
| Lecce          |                    0       |                    0.00021 |                        -0.16238 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     1.0655 |  0.6292 | 0.2787 |
| operational | dc_raw     |          10 |     1.1971 |  0.6958 | 0.3174 |
| operational | market     |           7 |     1.202  |  0.7317 | 0.3297 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 30 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          30 |     1.0183 |  0.6041 | 0.2198 |
| operational | dc_raw     |          30 |     1.0689 |  0.6316 | 0.2375 |
| operational | market     |          20 |     1.1242 |  0.6828 | 0.2696 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team   | away_team      | actual_result   |   predicted_probability_of_actual_outcome |
|:------------|:---------------|:----------------|------------------------------------------:|
| Venezia     | Napoli         | home_win        |                                    0.1438 |
| Juventus    | Lazio          | away_win        |                                    0.1982 |
| Udinese     | Lecce          | away_win        |                                    0.2153 |
| Monza       | Cagliari       | home_win        |                                    0.3178 |
| Frosinone   | Sassuolo       | home_win        |                                    0.3499 |
| Parma       | Torino         | away_win        |                                    0.3811 |
| Milan       | Atalanta       | home_win        |                                    0.4306 |
| Fiorentina  | Como           | away_win        |                                    0.4879 |
| Bologna     | Internazionale | away_win        |                                    0.6408 |
| Roma        | Genoa          | home_win        |                                    0.6737 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
