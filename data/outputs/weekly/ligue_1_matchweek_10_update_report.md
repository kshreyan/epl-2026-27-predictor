# LIGUE_1 Matchweek 10 Update Report

Generated: 2026-11-09T14:34:28+00:00

Locked 9 real result(s). 216 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| LOSC Lille             |                    0.02247 |                    0.10697 |                        -0.00022 |
| Olympique de Marseille |                    0.01753 |                    0.1232  |                        -0.00059 |
| Paris FC               |                    0.01063 |                    0.08518 |                        -0.00125 |
| OGC Nice               |                    0.00081 |                    0.02634 |                        -0.01571 |
| Stade Brestois 29      |                    0.00056 |                    0.02705 |                        -0.02846 |
| FC Lorient             |                    0.00046 |                    0.01783 |                        -0.04489 |
| Toulouse FC            |                    0.00039 |                    0.01881 |                        -0.03427 |
| Havre Athletic Club    |                    0       |                   -6e-05   |                         0.07501 |
| Estac Troyes           |                    0       |                   -0.00014 |                        -0.02922 |
| Le Mans FC             |                    0       |                   -0.00013 |                        -0.04368 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.9232 |  0.5603 | 0.2193 |
| operational | dc_raw     |           9 |     0.9557 |  0.5819 | 0.227  |
| operational | market     |           9 |     0.9212 |  0.5487 | 0.2151 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 54 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          54 |     0.8653 |  0.506  | 0.1905 |
| operational | dc_raw     |          54 |     0.8894 |  0.5246 | 0.1974 |
| operational | market     |          54 |     0.8575 |  0.4983 | 0.187  |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team           | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:--------------------|:-----------------------|:----------------|------------------------------------------:|
| Le Mans FC          | AS Monaco              | draw            |                                    0.2184 |
| RC Lens             | Olympique de Marseille | away_win        |                                    0.2939 |
| Stade Brestois 29   | Olympique Lyonnais     | home_win        |                                    0.3057 |
| Stade Rennais FC    | LOSC Lille             | away_win        |                                    0.3329 |
| Havre Athletic Club | FC Lorient             | away_win        |                                    0.38   |
| Toulouse FC         | RC Strasbourg Alsace   | home_win        |                                    0.4295 |
| Angers SCO          | OGC Nice               | away_win        |                                    0.4509 |
| AJ Auxerre          | Paris FC               | away_win        |                                    0.5124 |
| Paris Saint-Germain | Estac Troyes           | home_win        |                                    1      |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
