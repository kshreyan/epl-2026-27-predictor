# SERIE_A Matchweek 5 Update Report

Generated: 2026-09-21T07:38:38+00:00

Locked 10 real result(s). 330 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Internazionale |                          0 |                          0 |                               0 |
| Roma           |                          0 |                          0 |                               0 |
| Monza          |                          0 |                          0 |                               0 |
| Lecce          |                          0 |                          0 |                               0 |
| Frosinone      |                          0 |                          0 |                               0 |
| Parma          |                          0 |                          0 |                               0 |
| Genoa          |                          0 |                          0 |                               0 |
| Torino         |                          0 |                          0 |                               0 |
| Udinese        |                          0 |                          0 |                               0 |
| Fiorentina     |                          0 |                          0 |                               0 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     1.1298 |  0.6811 | 0.2344 |
| operational | dc_raw     |          10 |     1.1899 |  0.7241 | 0.2574 |
| operational | market     |           7 |     1.2539 |  0.7715 | 0.2836 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 10 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     1.1298 |  0.6811 | 0.2344 |
| operational | dc_raw     |          10 |     1.1899 |  0.7241 | 0.2574 |
| operational | market     |           7 |     1.2539 |  0.7715 | 0.2836 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team   | away_team      | actual_result   |   predicted_probability_of_actual_outcome |
|:------------|:---------------|:----------------|------------------------------------------:|
| Frosinone   | Como           | home_win        |                                    0.1589 |
| Fiorentina  | Napoli         | draw            |                                    0.2594 |
| Monza       | Sassuolo       | home_win        |                                    0.2601 |
| Udinese     | Cagliari       | away_win        |                                    0.2752 |
| Roma        | Internazionale | draw            |                                    0.278  |
| Bologna     | Torino         | draw            |                                    0.2821 |
| Parma       | Genoa          | home_win        |                                    0.3348 |
| Juventus    | Atalanta       | home_win        |                                    0.4612 |
| Venezia     | Lazio          | away_win        |                                    0.5454 |
| Milan       | Lecce          | home_win        |                                    0.6361 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
