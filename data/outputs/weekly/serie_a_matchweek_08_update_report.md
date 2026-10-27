# SERIE_A Matchweek 8 Update Report

Generated: 2026-10-27T11:10:24+00:00

Locked 10 real result(s). 300 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Como           |                    0.01201 |                    0.03592 |                         0       |
| Internazionale |                    0.01017 |                   -0.00053 |                         0       |
| Milan          |                    0.00894 |                    0.05319 |                        -4e-05   |
| Lazio          |                    0.00402 |                    0.01593 |                        -2e-05   |
| Juventus       |                    0.00333 |                    0.02963 |                        -0.0003  |
| Bologna        |                    5e-05   |                    0.00429 |                        -0.01949 |
| Venezia        |                    0       |                   -6e-05   |                         0.02774 |
| Monza          |                    0       |                   -0.00016 |                         0.02916 |
| Lecce          |                    0       |                   -0.00021 |                         0.0376  |
| Genoa          |                    0       |                    0.00013 |                        -0.07097 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.7108 |  0.3964 | 0.1241 |
| operational | dc_raw     |          10 |     0.7152 |  0.3933 | 0.1182 |
| operational | market     |           6 |     0.6365 |  0.3364 | 0.1362 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 40 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          40 |     0.9415 |  0.5521 | 0.1958 |
| operational | dc_raw     |          40 |     0.9805 |  0.5721 | 0.2077 |
| operational | market     |          26 |     1.0117 |  0.6029 | 0.2388 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team      | away_team   | actual_result   |   predicted_probability_of_actual_outcome |
|:---------------|:------------|:----------------|------------------------------------------:|
| Atalanta       | Frosinone   | draw            |                                    0.2793 |
| Napoli         | Roma        | draw            |                                    0.3186 |
| Cagliari       | Bologna     | away_win        |                                    0.3867 |
| Genoa          | Venezia     | home_win        |                                    0.4787 |
| Torino         | Monza       | home_win        |                                    0.49   |
| Udinese        | Milan       | away_win        |                                    0.5519 |
| Como           | Sassuolo    | home_win        |                                    0.6338 |
| Lecce          | Juventus    | away_win        |                                    0.6406 |
| Lazio          | Parma       | home_win        |                                    0.6489 |
| Internazionale | Fiorentina  | home_win        |                                    0.6972 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
