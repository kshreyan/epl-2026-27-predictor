# BUNDESLIGA Matchweek 10 Update Report

Generated: 2026-11-23T16:39:39+00:00

Locked 9 real result(s). 216 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                     |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-------------------------|---------------------------:|---------------------------:|--------------------------------:|
| Borussia Dortmund        |                    0.057   |                    0.00262 |                         0       |
| RB Leipzig               |                    0.02555 |                    0.05954 |                        -3e-05   |
| Bayer 04 Leverkusen      |                    0.00967 |                    0.0418  |                        -0.00024 |
| Sport-Club Freiburg      |                    0.00249 |                    0.02844 |                        -0.00079 |
| SV Werder Bremen         |                    0.00024 |                    0.01987 |                        -0.01692 |
| Eintracht Frankfurt      |                    2e-05   |                   -0.00092 |                        -0.0184  |
| SC Paderborn 07          |                    1e-05   |                   -0.00212 |                         0.0161  |
| Borussia Mönchengladbach |                    0       |                   -0.0002  |                         0.02954 |
| FC Augsburg              |                    0       |                    0.00249 |                        -0.0605  |
| 1. FC Union Berlin       |                    0       |                   -0.00038 |                         0.06576 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.962  |  0.58   | 0.1897 |
| operational | dc_raw     |           9 |     0.9718 |  0.5724 | 0.1887 |
| operational | market     |           5 |     1.2062 |  0.7214 | 0.2008 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 63 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          63 |     0.9928 |  0.595  | 0.207  |
| operational | dc_raw     |          63 |     0.9902 |  0.5875 | 0.2067 |
| operational | market     |          33 |     1.0124 |  0.6051 | 0.1894 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team                | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-------------------------|:--------------------|:----------------|------------------------------------------:|
| FC Bayern München        | 1. FC Köln          | draw            |                                    0.14   |
| FC Schalke 04            | VfB Stuttgart       | draw            |                                    0.2241 |
| SV Elversberg            | Sport-Club Freiburg | away_win        |                                    0.3083 |
| FC Augsburg              | 1. FSV Mainz 05     | home_win        |                                    0.4032 |
| Eintracht Frankfurt      | TSG Hoffenheim      | home_win        |                                    0.4221 |
| SV Werder Bremen         | Hamburger SV        | home_win        |                                    0.495  |
| 1. FC Union Berlin       | RB Leipzig          | away_win        |                                    0.542  |
| Borussia Mönchengladbach | Borussia Dortmund   | away_win        |                                    0.5832 |
| Bayer 04 Leverkusen      | SC Paderborn 07     | home_win        |                                    0.6742 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
