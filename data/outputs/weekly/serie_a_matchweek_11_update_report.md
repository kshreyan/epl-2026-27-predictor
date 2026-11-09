# SERIE_A Matchweek 11 Update Report

Generated: 2026-11-09T14:32:27+00:00

Locked 10 real result(s). 270 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Internazionale |                    0.08025 |                    0.02358 |                         0       |
| Roma           |                    0.00262 |                    0.03286 |                         0       |
| Cagliari       |                    1e-05   |                    0.00073 |                        -0.03935 |
| Fiorentina     |                    1e-05   |                   -0.00026 |                        -0.01032 |
| Udinese        |                    0       |                   -5e-05   |                         0.07732 |
| Parma          |                    0       |                   -8e-05   |                         0.03315 |
| Lecce          |                    0       |                    1e-05   |                        -0.03872 |
| Venezia        |                    0       |                    0       |                        -0.07491 |
| Sassuolo       |                    0       |                   -0.00017 |                         0.02544 |
| Monza          |                    0       |                   -2e-05   |                         0.01453 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.9025 |  0.5305 | 0.1612 |
| operational | dc_raw     |          10 |     0.9646 |  0.5709 | 0.1861 |
| operational | market     |           6 |     1.0928 |  0.6665 | 0.1799 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 70 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          70 |     0.9255 |  0.5392 | 0.1937 |
| operational | dc_raw     |          70 |     0.9385 |  0.546  | 0.1999 |
| operational | market     |          45 |     0.9594 |  0.5656 | 0.2125 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team      | away_team   | actual_result   |   predicted_probability_of_actual_outcome |
|:---------------|:------------|:----------------|------------------------------------------:|
| Fiorentina     | Juventus    | draw            |                                    0.2569 |
| Torino         | Lecce       | draw            |                                    0.2745 |
| Napoli         | Lazio       | draw            |                                    0.2874 |
| Cagliari       | Frosinone   | home_win        |                                    0.333  |
| Venezia        | Udinese     | home_win        |                                    0.3405 |
| Internazionale | Como        | home_win        |                                    0.4817 |
| Parma          | Bologna     | away_win        |                                    0.4842 |
| Genoa          | Milan       | away_win        |                                    0.5496 |
| Monza          | Atalanta    | away_win        |                                    0.5852 |
| Roma           | Sassuolo    | home_win        |                                    0.698  |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
