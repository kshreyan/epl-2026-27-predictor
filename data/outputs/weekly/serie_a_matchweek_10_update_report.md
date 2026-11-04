# SERIE_A Matchweek 10 Update Report

Generated: 2026-11-04T13:23:49+00:00

Locked 10 real result(s). 280 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:----------|---------------------------:|---------------------------:|--------------------------------:|
| Roma      |                    0.08694 |                    0.02226 |                         0       |
| Lazio     |                    0.02212 |                    0.03048 |                         0       |
| Como      |                    0.01854 |                   -0.01296 |                         0       |
| Milan     |                    0.01499 |                    0.10437 |                        -3e-05   |
| Juventus  |                    0.00532 |                    0.05859 |                        -0.00018 |
| Bologna   |                    6e-05   |                   -0.00308 |                        -0.00139 |
| Genoa     |                    2e-05   |                    0.00051 |                        -0.02769 |
| Lecce     |                    0       |                   -3e-05   |                         0.08842 |
| Cagliari  |                    0       |                   -0.00117 |                         0.01523 |
| Frosinone |                    0       |                    0.00034 |                        -0.04876 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          10 |     0.8968 |  0.511  | 0.2235 |
| operational | dc_raw     |          10 |     0.8413 |  0.4804 | 0.2137 |
| operational | market     |           7 |     0.689  |  0.376  | 0.1566 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 60 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          60 |     0.9293 |  0.5406 | 0.1991 |
| operational | dc_raw     |          60 |     0.9341 |  0.5419 | 0.2022 |
| operational | market     |          39 |     0.9389 |  0.55   | 0.2175 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team   | away_team      | actual_result   |   predicted_probability_of_actual_outcome |
|:------------|:---------------|:----------------|------------------------------------------:|
| Atalanta    | Parma          | away_win        |                                    0.1296 |
| Milan       | Internazionale | home_win        |                                    0.2389 |
| Sassuolo    | Fiorentina     | away_win        |                                    0.3787 |
| Lecce       | Genoa          | away_win        |                                    0.3893 |
| Juventus    | Napoli         | home_win        |                                    0.3922 |
| Frosinone   | Torino         | home_win        |                                    0.409  |
| Bologna     | Monza          | home_win        |                                    0.5723 |
| Lazio       | Cagliari       | home_win        |                                    0.6443 |
| Udinese     | Roma           | away_win        |                                    0.6487 |
| Como        | Venezia        | home_win        |                                    0.7275 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
