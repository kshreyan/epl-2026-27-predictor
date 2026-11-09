# BUNDESLIGA Matchweek 9 Update Report

Generated: 2026-11-09T14:33:29+00:00

Locked 9 real result(s). 225 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Bayern München        |                    0.00516 |                    0.00012 |                         0       |
| RB Leipzig               |                    0.00152 |                    0.03375 |                        -0.00012 |
| Bayer 04 Leverkusen      |                    0.00037 |                    0.03001 |                        -0.00025 |
| Sport-Club Freiburg      |                    5e-05   |                    0.01764 |                        -0.00202 |
| Hamburger SV             |                    2e-05   |                    0.00307 |                        -0.13526 |
| FC Augsburg              |                    1e-05   |                   -0.00993 |                         0.01473 |
| Borussia Mönchengladbach |                    0       |                   -0.00108 |                         0.07879 |
| 1. FC Köln               |                    0       |                   -0.00279 |                         0.0298  |
| 1. FC Union Berlin       |                    0       |                   -0.00126 |                         0.05085 |
| FC Schalke 04            |                    0       |                   -0.0015  |                         0.01323 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.6684 |  0.3563 | 0.1229 |
| operational | dc_raw     |           9 |     0.5784 |  0.2954 | 0.1016 |
| operational | market     |           4 |     0.4443 |  0.1955 | 0.0799 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 54 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          54 |     0.998  |  0.5975 | 0.2099 |
| operational | dc_raw     |          54 |     0.9933 |  0.59   | 0.2097 |
| operational | market     |          28 |     0.9778 |  0.5844 | 0.1874 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team           | away_team                | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------|:-------------------------|:----------------|------------------------------------------:|
| SC Paderborn 07     | Eintracht Frankfurt      | draw            |                                    0.2585 |
| Hamburger SV        | Borussia Mönchengladbach | home_win        |                                    0.3612 |
| 1. FC Köln          | Bayer 04 Leverkusen      | away_win        |                                    0.5018 |
| Sport-Club Freiburg | 1. FC Union Berlin       | home_win        |                                    0.5348 |
| TSG Hoffenheim      | FC Schalke 04            | home_win        |                                    0.5664 |
| VfB Stuttgart       | SV Werder Bremen         | home_win        |                                    0.5897 |
| RB Leipzig          | FC Augsburg              | home_win        |                                    0.6471 |
| 1. FSV Mainz 05     | FC Bayern München        | away_win        |                                    0.6602 |
| Borussia Dortmund   | SV Elversberg            | home_win        |                                    0.6828 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
