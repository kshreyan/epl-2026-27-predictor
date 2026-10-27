# EPL Matchweek 8 Update Report

Generated: 2026-10-27T11:08:56+00:00

Locked 10 real result(s). 300 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team              |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal           |                    0.12293 |                    0.01293 |                         0       |
| Liverpool         |                    0.01406 |                    0.13408 |                        -0.00048 |
| Aston Villa       |                    0.00082 |                    0.05997 |                        -0.01226 |
| AFC Bournemouth   |                    0.00054 |                    0.04505 |                        -0.02929 |
| Newcastle United  |                    0.00039 |                    0.02879 |                        -0.02359 |
| Fulham            |                    2e-05   |                    0.00298 |                        -0.04354 |
| Tottenham Hotspur |                    2e-05   |                    0.00924 |                        -0.08685 |
| Hull City         |                    0       |                   -0.00037 |                         0.00674 |
| Sunderland        |                    0       |                   -0.00119 |                         0.00827 |
| Coventry City     |                    0       |                   -0.00053 |                         0.04431 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.1331 |   0.6908 |   0.245  |
| operational | dc_raw     |          10 |     1.1093 |   0.6777 |   0.2393 |
| operational | market     |          10 |     1.1423 |   0.6998 |   0.2492 |
| preseason   | production |          10 |     1.1355 |   0.6994 |   0.2386 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 80 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          80 |     1.3285 |   0.6082 |   0.2056 |
| operational | dc_raw     |          80 |     1.0625 |   0.6164 |   0.2121 |
| operational | market     |          80 |     1.0199 |   0.612  |   0.2045 |
| preseason   | production |          80 |     1.0382 |   0.6215 |   0.2101 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Chelsea           | Tottenham Hotspur      | away_win        |                                    0.1939 |
| Aston Villa       | Manchester City        | home_win        |                                    0.2397 |
| Manchester United | AFC Bournemouth        | away_win        |                                    0.2577 |
| Ipswich Town      | Nottingham Forest      | draw            |                                    0.2648 |
| Hull City         | Brentford              | draw            |                                    0.2705 |
| Sunderland        | Leeds United           | draw            |                                    0.2914 |
| Crystal Palace    | Newcastle United       | away_win        |                                    0.3777 |
| Liverpool         | Brighton & Hove Albion | home_win        |                                    0.425  |
| Coventry City     | Fulham                 | away_win        |                                    0.4592 |
| Arsenal           | Everton                | home_win        |                                    0.6509 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
