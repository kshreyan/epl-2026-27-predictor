# BUNDESLIGA Matchweek 7 Update Report

Generated: 2026-10-27T11:11:10+00:00

Locked 9 real result(s). 243 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Bayern München        |                    0.02737 |                    0.00082 |                         0       |
| RB Leipzig               |                    0.00224 |                    0.14017 |                        -0.00083 |
| Borussia Dortmund        |                    0.00084 |                    0.03848 |                         0       |
| TSG Hoffenheim           |                    9e-05   |                    0.04827 |                        -0.04128 |
| SV Werder Bremen         |                    5e-05   |                    0.03053 |                        -0.04847 |
| 1. FC Köln               |                    0       |                   -0.0012  |                         0.04768 |
| 1. FC Union Berlin       |                    0       |                    0.00022 |                         0.00818 |
| Borussia Mönchengladbach |                    0       |                    0.00198 |                        -0.15351 |
| SC Paderborn 07          |                   -1e-05   |                    0.00018 |                        -0.0283  |
| Hamburger SV             |                   -2e-05   |                   -0.00553 |                         0.07634 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.0577 |  0.6334 | 0.2342 |
| operational | dc_raw     |           9 |     1.0607 |  0.6427 | 0.2449 |
| operational | market     |           4 |     0.912  |  0.5277 | 0.1123 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 36 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          36 |     1.0455 |  0.6326 | 0.2272 |
| operational | dc_raw     |          36 |     1.0757 |  0.6449 | 0.2346 |
| operational | market     |          19 |     1.0589 |  0.6436 | 0.208  |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team           | away_team                | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------|:-------------------------|:----------------|------------------------------------------:|
| VfB Stuttgart       | Borussia Mönchengladbach | away_win        |                                    0.1854 |
| 1. FSV Mainz 05     | SV Werder Bremen         | away_win        |                                    0.2407 |
| FC Augsburg         | 1. FC Union Berlin       | draw            |                                    0.2578 |
| 1. FC Köln          | FC Schalke 04            | draw            |                                    0.2621 |
| TSG Hoffenheim      | Bayer 04 Leverkusen      | home_win        |                                    0.288  |
| SC Paderborn 07     | Hamburger SV             | home_win        |                                    0.3408 |
| RB Leipzig          | SV Elversberg            | home_win        |                                    0.6116 |
| Sport-Club Freiburg | FC Bayern München        | away_win        |                                    0.6234 |
| Borussia Dortmund   | Eintracht Frankfurt      | home_win        |                                    0.6507 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
