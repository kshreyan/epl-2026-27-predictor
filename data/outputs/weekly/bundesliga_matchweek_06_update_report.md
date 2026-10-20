# BUNDESLIGA Matchweek 6 Update Report

Generated: 2026-10-20T10:33:06+00:00

Locked 9 real result(s). 252 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Bayern München        |                    0.06527 |                    0.00286 |                         0       |
| 1. FSV Mainz 05          |                    6e-05   |                    0.04103 |                        -0.01443 |
| 1. FC Union Berlin       |                    0       |                    0.00037 |                        -0.00636 |
| Borussia Mönchengladbach |                    0       |                   -0.00089 |                         0.11707 |
| Hamburger SV             |                    0       |                    0.00857 |                        -0.10201 |
| TSG Hoffenheim           |                   -1e-05   |                    0.01765 |                        -0.03853 |
| Eintracht Frankfurt      |                   -1e-05   |                    0.01458 |                        -0.01528 |
| 1. FC Köln               |                   -1e-05   |                   -0.00219 |                         0.05113 |
| SV Werder Bremen         |                   -3e-05   |                   -0.00446 |                         0.02102 |
| SC Paderborn 07          |                   -0.00011 |                   -0.00463 |                         0.00223 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.9608 |  0.577  | 0.2003 |
| operational | dc_raw     |           9 |     0.9116 |  0.549  | 0.1927 |
| operational | market     |           5 |     0.968  |  0.5846 | 0.213  |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 27 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          27 |     1.0414 |  0.6324 | 0.2248 |
| operational | dc_raw     |          27 |     1.0807 |  0.6457 | 0.2311 |
| operational | market     |          15 |     1.0981 |  0.6745 | 0.2335 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-------------------------|:--------------------|:----------------|------------------------------------------:|
| 1. FC Union Berlin       | Borussia Dortmund   | draw            |                                    0.2261 |
| Hamburger SV             | VfB Stuttgart       | home_win        |                                    0.2457 |
| SV Werder Bremen         | SC Paderborn 07     | draw            |                                    0.2516 |
| Borussia Mönchengladbach | TSG Hoffenheim      | away_win        |                                    0.3352 |
| FC Schalke 04            | 1. FSV Mainz 05     | away_win        |                                    0.4057 |
| SV Elversberg            | FC Augsburg         | home_win        |                                    0.4411 |
| Eintracht Frankfurt      | 1. FC Köln          | home_win        |                                    0.5112 |
| Bayer 04 Leverkusen      | Sport-Club Freiburg | home_win        |                                    0.5727 |
| FC Bayern München        | RB Leipzig          | home_win        |                                    0.7156 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
