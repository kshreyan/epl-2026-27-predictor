# BUNDESLIGA Matchweek 8 Update Report

Generated: 2026-11-02T13:58:41+00:00

Locked 9 real result(s). 234 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| Borussia Dortmund        |                    0.02014 |                    0.01409 |                        -2e-05   |
| RB Leipzig               |                    0.00717 |                    0.05943 |                        -0.00042 |
| Sport-Club Freiburg      |                    0.00105 |                    0.06255 |                        -0.00535 |
| VfB Stuttgart            |                    0.00102 |                    0.10151 |                        -0.0081  |
| SV Werder Bremen         |                    0.00017 |                    0.02652 |                        -0.03084 |
| Eintracht Frankfurt      |                    6e-05   |                    0.01186 |                        -0.0275  |
| SV Elversberg            |                    1e-05   |                    0.00141 |                        -0.08288 |
| Borussia Mönchengladbach |                    0       |                   -0.00128 |                         0.03186 |
| FC Schalke 04            |                    0       |                   -0.00272 |                         0.033   |
| 1. FC Union Berlin       |                    0       |                   -0.00117 |                         0.01746 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.1376 |  0.6984 | 0.2278 |
| operational | dc_raw     |           9 |     1.0785 |  0.6651 | 0.2185 |
| operational | market     |           5 |     1.0966 |  0.6706 | 0.1949 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 45 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          45 |     1.0639 |  0.6458 | 0.2273 |
| operational | dc_raw     |          45 |     1.0763 |  0.649  | 0.2313 |
| operational | market     |          24 |     1.0668 |  0.6492 | 0.2053 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-------------------------|:--------------------|:----------------|------------------------------------------:|
| FC Bayern München        | Borussia Dortmund   | draw            |                                    0.1968 |
| Bayer 04 Leverkusen      | VfB Stuttgart       | away_win        |                                    0.2064 |
| Borussia Mönchengladbach | SC Paderborn 07     | draw            |                                    0.2329 |
| 1. FC Union Berlin       | 1. FC Köln          | draw            |                                    0.2616 |
| SV Werder Bremen         | TSG Hoffenheim      | home_win        |                                    0.3411 |
| FC Augsburg              | Sport-Club Freiburg | away_win        |                                    0.342  |
| SV Elversberg            | 1. FSV Mainz 05     | home_win        |                                    0.4079 |
| FC Schalke 04            | RB Leipzig          | away_win        |                                    0.5389 |
| Eintracht Frankfurt      | Hamburger SV        | home_win        |                                    0.5638 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
