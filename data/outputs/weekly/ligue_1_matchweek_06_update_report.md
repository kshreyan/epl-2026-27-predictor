# LIGUE_1 Matchweek 6 Update Report

Generated: 2026-10-13T13:04:19+00:00

Locked 9 real result(s). 252 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain    |                    0.04721 |                    0.01054 |                         0       |
| Stade Rennais FC       |                    0.0146  |                    0.07881 |                        -0.00454 |
| LOSC Lille             |                    0.01135 |                    0.03818 |                        -0.0008  |
| RC Lens                |                    0.00926 |                    0.06282 |                        -0.00387 |
| Olympique de Marseille |                    0.00446 |                    0.03894 |                        -0.00624 |
| Stade Brestois 29      |                    0.00087 |                    0.02011 |                        -0.07987 |
| FC Lorient             |                    0.00082 |                    0.01619 |                        -0.06281 |
| OGC Nice               |                    0.00026 |                    0.00847 |                        -0.07954 |
| Toulouse FC            |                    7e-05   |                    0.00485 |                        -0.021   |
| Estac Troyes           |                    1e-05   |                   -0.0003  |                         0.03365 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.7501 |  0.4219 | 0.1541 |
| operational | dc_raw     |           9 |     0.7467 |  0.4228 | 0.1539 |
| operational | market     |           9 |     0.7334 |  0.4131 | 0.1508 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 18 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          18 |     0.8041 |  0.4585 | 0.1846 |
| operational | dc_raw     |          18 |     0.812  |  0.4663 | 0.1878 |
| operational | market     |          18 |     0.7909 |  0.4511 | 0.1811 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team           | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------|:-----------------------|:----------------|------------------------------------------:|
| AS Monaco           | Toulouse FC            | draw            |                                    0.2347 |
| FC Lorient          | Paris FC               | home_win        |                                    0.3315 |
| OGC Nice            | RC Strasbourg Alsace   | home_win        |                                    0.3832 |
| RC Lens             | Olympique Lyonnais     | home_win        |                                    0.4536 |
| Stade Brestois 29   | Angers SCO             | home_win        |                                    0.4957 |
| Estac Troyes        | Olympique de Marseille | away_win        |                                    0.5555 |
| Stade Rennais FC    | AJ Auxerre             | home_win        |                                    0.6049 |
| LOSC Lille          | Havre Athletic Club    | home_win        |                                    0.6362 |
| Paris Saint-Germain | Le Mans FC             | home_win        |                                    0.8161 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
