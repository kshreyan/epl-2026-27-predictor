# LIGUE_1 Matchweek 8 Update Report

Generated: 2026-10-27T11:11:53+00:00

Locked 9 real result(s). 234 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain |                    0.07351 |                    0.02024 |                         0       |
| Stade Rennais FC    |                    0.00983 |                    0.10552 |                        -0.0028  |
| RC Lens             |                    0.00467 |                    0.06617 |                        -0.00122 |
| OGC Nice            |                    0.00035 |                    0.01114 |                        -0.06008 |
| Havre Athletic Club |                    0       |                   -7e-05   |                         0.01287 |
| Le Mans FC          |                   -1e-05   |                   -0.00028 |                        -0.01157 |
| Angers SCO          |                   -1e-05   |                   -0.00017 |                        -0.00482 |
| Estac Troyes        |                   -2e-05   |                   -0.00026 |                        -0.00752 |
| AJ Auxerre          |                   -0.00023 |                   -0.0049  |                         0.01748 |
| Stade Brestois 29   |                   -0.00074 |                   -0.01739 |                         0.03152 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.9964 |  0.601  | 0.1642 |
| operational | dc_raw     |           9 |     1.0762 |  0.6587 | 0.1816 |
| operational | market     |           9 |     0.9921 |  0.591  | 0.1602 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 36 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          36 |     0.8664 |  0.5044 | 0.181  |
| operational | dc_raw     |          36 |     0.8817 |  0.5181 | 0.1852 |
| operational | market     |          36 |     0.8671 |  0.5038 | 0.1808 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team            | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:---------------------|:----------------|------------------------------------------:|
| Toulouse FC            | Estac Troyes         | draw            |                                    0.2233 |
| AJ Auxerre             | Le Mans FC           | draw            |                                    0.2335 |
| AS Monaco              | LOSC Lille           | draw            |                                    0.2796 |
| Stade Brestois 29      | OGC Nice             | away_win        |                                    0.2963 |
| Angers SCO             | FC Lorient           | draw            |                                    0.297  |
| RC Lens                | Paris FC             | home_win        |                                    0.4663 |
| Stade Rennais FC       | RC Strasbourg Alsace | home_win        |                                    0.5238 |
| Olympique de Marseille | Havre Athletic Club  | home_win        |                                    0.6333 |
| Paris Saint-Germain    | Olympique Lyonnais   | home_win        |                                    0.6426 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
