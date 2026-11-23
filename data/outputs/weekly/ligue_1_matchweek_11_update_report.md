# LIGUE_1 Matchweek 11 Update Report

Generated: 2026-11-23T16:40:10+00:00

Locked 9 real result(s). 207 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain |                    0.04951 |                    0.00707 |                         0       |
| Paris FC            |                    0.01842 |                    0.15089 |                        -0.00034 |
| Olympique Lyonnais  |                    0.01153 |                    0.14951 |                        -0.00033 |
| Stade Brestois 29   |                    0.00098 |                    0.04957 |                        -0.00918 |
| AJ Auxerre          |                    1e-05   |                    0.00038 |                        -0.01919 |
| Estac Troyes        |                    0       |                    0.00025 |                        -0.06672 |
| Havre Athletic Club |                    0       |                   -1e-05   |                         0.09394 |
| Angers SCO          |                    0       |                   -1e-05   |                         0.11258 |
| Le Mans FC          |                   -1e-05   |                    0.00062 |                        -0.1314  |
| Toulouse FC         |                   -2e-05   |                    0.00607 |                        -0.00187 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     1.2801 |  0.7831 | 0.2718 |
| operational | dc_raw     |           9 |     1.2979 |  0.7912 | 0.2788 |
| operational | market     |           9 |     1.1228 |  0.685  | 0.2285 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 63 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          63 |     0.9245 |  0.5456 | 0.2021 |
| operational | dc_raw     |          63 |     0.9478 |  0.5627 | 0.209  |
| operational | market     |          63 |     0.8954 |  0.5249 | 0.1929 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:--------------------|:----------------|------------------------------------------:|
| Olympique de Marseille | Le Mans FC          | away_win        |                                    0.1309 |
| AS Monaco              | AJ Auxerre          | draw            |                                    0.2084 |
| RC Lens                | Toulouse FC         | draw            |                                    0.2394 |
| FC Lorient             | Stade Rennais FC    | draw            |                                    0.2407 |
| LOSC Lille             | Olympique Lyonnais  | away_win        |                                    0.2431 |
| Estac Troyes           | Havre Athletic Club | home_win        |                                    0.2477 |
| RC Strasbourg Alsace   | Stade Brestois 29   | away_win        |                                    0.2819 |
| OGC Nice               | Paris Saint-Germain | away_win        |                                    0.5657 |
| Paris FC               | Angers SCO          | home_win        |                                    0.6572 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
