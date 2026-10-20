# LIGUE_1 Matchweek 7 Update Report

Generated: 2026-10-20T10:33:49+00:00

Locked 9 real result(s). 243 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain    |                    0.08281 |                    0.02242 |                        -2e-05   |
| Paris FC               |                    0.00696 |                    0.06184 |                        -0.0084  |
| Olympique de Marseille |                    0.00693 |                    0.07085 |                        -0.00579 |
| Olympique Lyonnais     |                    0.00613 |                    0.04657 |                        -0.00098 |
| RC Lens                |                    0.00317 |                    0.03523 |                        -0.00236 |
| Toulouse FC            |                    0.00135 |                    0.02947 |                        -0.04486 |
| FC Lorient             |                    0.00085 |                    0.0198  |                        -0.04496 |
| AJ Auxerre             |                    0.00011 |                    0.00663 |                        -0.11664 |
| Angers SCO             |                   -1e-05   |                   -0.00067 |                         0.0696  |
| Havre Athletic Club    |                   -1e-05   |                   -0.00073 |                         0.09907 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |           9 |     0.8609 |  0.4995 | 0.1908 |
| operational | dc_raw     |           9 |     0.8267 |  0.4812 | 0.1834 |
| operational | market     |           9 |     0.8946 |  0.5221 | 0.2009 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

Cumulative, all 27 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          27 |     0.823  |  0.4722 | 0.1866 |
| operational | dc_raw     |          27 |     0.8169 |  0.4713 | 0.1863 |
| operational | market     |          27 |     0.8255 |  0.4748 | 0.1877 |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team            | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:---------------------|:-----------------------|:----------------|------------------------------------------:|
| LOSC Lille           | Stade Brestois 29      | draw            |                                    0.2364 |
| FC Lorient           | AS Monaco              | home_win        |                                    0.2976 |
| Havre Athletic Club  | AJ Auxerre             | away_win        |                                    0.326  |
| Le Mans FC           | Toulouse FC            | away_win        |                                    0.3995 |
| Paris FC             | Stade Rennais FC       | home_win        |                                    0.4313 |
| Angers SCO           | Olympique de Marseille | away_win        |                                    0.4847 |
| Olympique Lyonnais   | OGC Nice               | home_win        |                                    0.5757 |
| RC Strasbourg Alsace | Paris Saint-Germain    | away_win        |                                    0.6137 |
| Estac Troyes         | RC Lens                | away_win        |                                    0.6377 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
