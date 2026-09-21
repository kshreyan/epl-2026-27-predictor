# LIGUE_1 Matchweek 5 Update Report

Generated: 2026-09-21T07:40:00+00:00

Locked 9 real result(s). 261 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain |                    0.06173 |                    0.03935 |                        -3e-05   |
| Olympique Lyonnais  |                    0.03836 |                    0.1585  |                        -0.00196 |
| AS Monaco           |                    0.03294 |                    0.09861 |                        -0.0005  |
| Paris FC            |                    0.00653 |                    0.06575 |                        -0.00623 |
| Toulouse FC         |                    0.00035 |                    0.0107  |                        -0.0235  |
| AJ Auxerre          |                    0.00022 |                    0.00719 |                        -0.05895 |
| OGC Nice            |                    0.00021 |                    0.00616 |                        -0.08529 |
| Angers SCO          |                    4e-05   |                    0.00142 |                        -0.07324 |
| Le Mans FC          |                    0       |                    0.00104 |                        -0.03045 |
| Havre Athletic Club |                   -4e-05   |                   -0.00087 |                         0.07054 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.858  |  0.4952 | 0.215  |
| operational | dc_raw     |           9 |     0.8774 |  0.5097 | 0.2217 |
| operational | market     |           9 |     0.8484 |  0.4892 | 0.2114 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 9 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.858  |  0.4952 | 0.215  |
| operational | dc_raw     |           9 |     0.8774 |  0.5097 | 0.2217 |
| operational | market     |           9 |     0.8484 |  0.4892 | 0.2114 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team            | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:---------------------|:----------------|------------------------------------------:|
| OGC Nice               | LOSC Lille           | home_win        |                                    0.2456 |
| AJ Auxerre             | Stade Brestois 29    | home_win        |                                    0.3641 |
| Le Mans FC             | FC Lorient           | home_win        |                                    0.3671 |
| AS Monaco              | RC Lens              | home_win        |                                    0.43   |
| Paris FC               | RC Strasbourg Alsace | home_win        |                                    0.4573 |
| Olympique Lyonnais     | Stade Rennais FC     | home_win        |                                    0.4697 |
| Angers SCO             | Estac Troyes         | home_win        |                                    0.4812 |
| Toulouse FC            | Havre Athletic Club  | home_win        |                                    0.5181 |
| Olympique de Marseille | Paris Saint-Germain  | away_win        |                                    0.5858 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
