# SERIE_A Matchweek 12 Update Report

Generated: 2026-11-23T16:39:09+00:00

Locked 9 real result(s). 261 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------|---------------------------:|---------------------------:|--------------------------------:|
| Roma     |                    0.08447 |                    0.01141 |                         0       |
| Lazio    |                    0.01878 |                    0.02187 |                         0       |
| Milan    |                    0.01354 |                    0.04025 |                         0       |
| Como     |                    0.00842 |                   -0.008   |                         0       |
| Juventus |                    0.00168 |                    0.01113 |                        -6e-05   |
| Venezia  |                    0       |                    0       |                         0.00737 |
| Lecce    |                    0       |                   -1e-05   |                         0.03386 |
| Monza    |                    0       |                   -3e-05   |                        -0.01323 |
| Udinese  |                    0       |                    1e-05   |                        -0.06312 |
| Parma    |                    0       |                   -2e-05   |                         0.03682 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.7192 |  0.4039 | 0.1171 |
| operational | dc_raw     |           9 |     0.7271 |  0.4029 | 0.1169 |
| operational | market     |           6 |     0.6542 |  0.3554 | 0.1121 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 79 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          79 |     0.902  |  0.5238 | 0.185  |
| operational | dc_raw     |          79 |     0.9144 |  0.5297 | 0.1904 |
| operational | market     |          51 |     0.9235 |  0.5408 | 0.2006 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team   | away_team      | actual_result   |   predicted_probability_of_actual_outcome |
|:------------|:---------------|:----------------|------------------------------------------:|
| Atalanta    | Internazionale | draw            |                                    0.2406 |
| Bologna     | Udinese        | draw            |                                    0.2622 |
| Sassuolo    | Genoa          | away_win        |                                    0.3145 |
| Milan       | Frosinone      | home_win        |                                    0.5925 |
| Napoli      | Torino         | home_win        |                                    0.6074 |
| Como        | Cagliari       | home_win        |                                    0.6512 |
| Lazio       | Lecce          | home_win        |                                    0.676  |
| Parma       | Roma           | away_win        |                                    0.6977 |
| Juventus    | Venezia        | home_win        |                                    0.7044 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
