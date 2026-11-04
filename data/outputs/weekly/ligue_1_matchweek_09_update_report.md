# LIGUE_1 Matchweek 9 Update Report

Generated: 2026-11-04T13:24:39+00:00

Locked 9 real result(s). 225 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain    |                    0.06584 |                    0.01174 |                         0       |
| Paris FC               |                    0.00685 |                    0.10121 |                        -0.0052  |
| LOSC Lille             |                    0.00637 |                    0.09328 |                        -0.00054 |
| Olympique de Marseille |                    0.00121 |                    0.06756 |                        -0.00143 |
| RC Strasbourg Alsace   |                    0.00081 |                    0.03728 |                        -0.02663 |
| OGC Nice               |                    0.00037 |                    0.02358 |                        -0.04939 |
| Stade Brestois 29      |                    0.0002  |                    0.0145  |                        -0.05518 |
| Angers SCO             |                    0       |                   -0.00019 |                         0.02861 |
| Havre Athletic Club    |                    0       |                   -0.00016 |                         0.05493 |
| Estac Troyes           |                   -1e-05   |                   -0.00011 |                        -0.0781  |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.8029 |  0.4584 | 0.1997 |
| operational | dc_raw     |           9 |     0.854  |  0.4932 | 0.2168 |
| operational | market     |           9 |     0.7555 |  0.4256 | 0.1835 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 45 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          45 |     0.8537 |  0.4952 | 0.1847 |
| operational | dc_raw     |          45 |     0.8762 |  0.5132 | 0.1915 |
| operational | market     |          45 |     0.8448 |  0.4882 | 0.1814 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:--------------------|:----------------|------------------------------------------:|
| FC Lorient             | Stade Brestois 29   | away_win        |                                    0.3057 |
| Estac Troyes           | Le Mans FC          | home_win        |                                    0.3281 |
| OGC Nice               | Stade Rennais FC    | home_win        |                                    0.3435 |
| LOSC Lille             | RC Lens             | home_win        |                                    0.3994 |
| Paris FC               | AS Monaco           | home_win        |                                    0.407  |
| Olympique de Marseille | Toulouse FC         | home_win        |                                    0.5192 |
| RC Strasbourg Alsace   | AJ Auxerre          | home_win        |                                    0.5292 |
| Olympique Lyonnais     | Angers SCO          | home_win        |                                    0.6725 |
| Havre Athletic Club    | Paris Saint-Germain | away_win        |                                    0.7028 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
