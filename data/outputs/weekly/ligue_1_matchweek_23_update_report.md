# LIGUE_1 Matchweek 23 Update Report

Generated: 2026-11-09T14:35:01+00:00

Locked 1 real result(s). 215 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| LOSC Lille             |                    0.01265 |                   -0.00241 |                         0       |
| Olympique de Marseille |                    0.0086  |                    9e-05   |                         5e-05   |
| Paris FC               |                    0.00621 |                    0.00025 |                        -0.00012 |
| Olympique Lyonnais     |                    0.004   |                    0.00042 |                        -6e-05   |
| AS Monaco              |                    0.00364 |                   -0.00176 |                         8e-05   |
| RC Lens                |                    0.00197 |                   -0.00195 |                        -1e-05   |
| Stade Brestois 29      |                    0.00031 |                   -0.0011  |                         0.00017 |
| OGC Nice               |                    0.0003  |                    0.00036 |                         0.0002  |
| Stade Rennais FC       |                    0.00018 |                    0.01025 |                        -0.00082 |
| FC Lorient             |                    0.00017 |                    0.00017 |                         0.00075 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (1 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |           1 |     1.576  |   0.9989 |   0.1849 |
| operational | dc_raw     |           1 |     1.5818 |   1.0136 |   0.1913 |
| operational | market     |           0 |   nan      | nan      | nan      |
| preseason   | production |           0 |            |          |          |
| preseason   | dc_raw     |           0 |            |          |          |
| preseason   | market     |           0 |            |          |          |

Cumulative, all 55 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |   brier |    rps |
|:------------|:-----------|------------:|-----------:|--------:|-------:|
| operational | production |          55 |     0.8782 |  0.515  | 0.1904 |
| operational | dc_raw     |          55 |     0.902  |  0.5335 | 0.1973 |
| operational | market     |          54 |     0.8575 |  0.4983 | 0.187  |
| preseason   | production |           0 |            |         |        |
| preseason   | dc_raw     |           0 |            |         |        |
| preseason   | market     |           0 |            |         |        |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team        | away_team           | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------|:--------------------|:----------------|------------------------------------------:|
| Stade Rennais FC | Paris Saint-Germain | draw            |                                    0.2068 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
