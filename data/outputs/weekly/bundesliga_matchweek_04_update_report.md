# BUNDESLIGA Matchweek 4 Update Report

Generated: 2026-09-21T07:39:19+00:00

Locked 9 real result(s). 270 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Bayern München        |                    0.13434 |                    0.0058  |                         0       |
| Borussia Dortmund        |                    0.03898 |                    0.11753 |                        -2e-05   |
| Bayer 04 Leverkusen      |                    0.00533 |                    0.19178 |                        -0.00022 |
| 1. FSV Mainz 05          |                    0.00025 |                    0.06153 |                        -0.01286 |
| SV Werder Bremen         |                    3e-05   |                    0.01327 |                        -0.01796 |
| 1. FC Union Berlin       |                    0       |                   -0.00043 |                         0.16706 |
| Hamburger SV             |                    0       |                    0.00168 |                        -0.02256 |
| 1. FC Köln               |                   -3e-05   |                   -0.00239 |                         0.11402 |
| Borussia Mönchengladbach |                   -3e-05   |                   -0.0005  |                         0.12098 |
| Sport-Club Freiburg      |                   -0.00017 |                    0.06796 |                         6e-05   |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.0395 |  0.6259 | 0.2279 |
| operational | dc_raw     |           9 |     1.181  |  0.6691 | 0.2432 |
| operational | market     |           5 |     0.8939 |  0.5367 | 0.1939 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 9 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.0395 |  0.6259 | 0.2279 |
| operational | dc_raw     |           9 |     1.181  |  0.6691 | 0.2432 |
| operational | market     |           5 |     0.8939 |  0.5367 | 0.1939 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-------------------------|:--------------------|:----------------|------------------------------------------:|
| SC Paderborn 07          | TSG Hoffenheim      | home_win        |                                    0.1898 |
| FC Schalke 04            | SV Elversberg       | draw            |                                    0.2471 |
| Eintracht Frankfurt      | Sport-Club Freiburg | draw            |                                    0.2618 |
| Borussia Mönchengladbach | 1. FSV Mainz 05     | away_win        |                                    0.3437 |
| Hamburger SV             | 1. FC Köln          | home_win        |                                    0.3628 |
| VfB Stuttgart            | Borussia Dortmund   | away_win        |                                    0.3874 |
| SV Werder Bremen         | FC Augsburg         | home_win        |                                    0.3966 |
| Bayer 04 Leverkusen      | RB Leipzig          | home_win        |                                    0.435  |
| FC Bayern München        | 1. FC Union Berlin  | home_win        |                                    0.8453 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
