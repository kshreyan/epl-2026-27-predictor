# BUNDESLIGA Matchweek 5 Update Report

Generated: 2026-10-13T13:03:32+00:00

Locked 9 real result(s). 261 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| Bayer 04 Leverkusen      |                    0.02229 |                    0.03633 |                        -0.00027 |
| RB Leipzig               |                    0.01319 |                    0.13859 |                        -0.0021  |
| VfB Stuttgart            |                    0.00367 |                    0.0304  |                        -0.00213 |
| Sport-Club Freiburg      |                    0.00149 |                   -0.00409 |                        -0.00274 |
| FC Augsburg              |                    0.00013 |                    0.00478 |                        -0.01603 |
| Hamburger SV             |                    3e-05   |                    0.00368 |                        -0.18052 |
| SV Werder Bremen         |                    3e-05   |                    0.00446 |                        -0.0333  |
| 1. FC Köln               |                    2e-05   |                    0.00202 |                        -0.07858 |
| 1. FC Union Berlin       |                    0       |                    0.00059 |                        -0.08094 |
| Borussia Mönchengladbach |                    0       |                   -0.00225 |                         0.07576 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.1239 |  0.6942 | 0.2463 |
| operational | dc_raw     |           9 |     1.1496 |  0.7189 | 0.2574 |
| operational | market     |           5 |     1.4324 |  0.9021 | 0.2938 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 18 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          18 |     1.0817 |  0.6601 | 0.2371 |
| operational | dc_raw     |          18 |     1.1653 |  0.694  | 0.2503 |
| operational | market     |          10 |     1.1631 |  0.7194 | 0.2438 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team           | away_team                | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------|:-------------------------|:----------------|------------------------------------------:|
| TSG Hoffenheim      | Hamburger SV             | away_win        |                                    0.1584 |
| FC Augsburg         | FC Bayern München        | draw            |                                    0.1623 |
| Borussia Dortmund   | SV Werder Bremen         | draw            |                                    0.178  |
| 1. FC Union Berlin  | SV Elversberg            | home_win        |                                    0.3287 |
| 1. FC Köln          | Borussia Mönchengladbach | home_win        |                                    0.3812 |
| 1. FSV Mainz 05     | Bayer 04 Leverkusen      | away_win        |                                    0.4313 |
| Sport-Club Freiburg | FC Schalke 04            | home_win        |                                    0.5053 |
| SC Paderborn 07     | VfB Stuttgart            | away_win        |                                    0.5459 |
| RB Leipzig          | Eintracht Frankfurt      | home_win        |                                    0.5932 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
