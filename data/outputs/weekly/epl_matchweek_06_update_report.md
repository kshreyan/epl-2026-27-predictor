# EPL Matchweek 6 Update Report

Generated: 2026-10-13T13:01:56+00:00

Locked 10 real result(s). 320 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Manchester City        |                    0.07778 |                    0.02142 |                         0       |
| Brighton & Hove Albion |                    0.0045  |                    0.14089 |                        -0.00105 |
| Chelsea                |                    0.00155 |                    0.10653 |                        -0.00855 |
| Crystal Palace         |                    8e-05   |                    0.01134 |                        -0.06269 |
| Tottenham Hotspur      |                   -2e-05   |                    0.00086 |                         0.00096 |
| Coventry City          |                   -2e-05   |                    0.00042 |                        -0.08762 |
| Ipswich Town           |                   -4e-05   |                    0.00039 |                        -0.09416 |
| Hull City              |                   -8e-05   |                   -0.00106 |                        -0.03679 |
| Fulham                 |                   -8e-05   |                   -0.00627 |                         0.08798 |
| Sunderland             |                   -0.00028 |                   -0.01231 |                         0.07758 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.096  |   0.663  |   0.2316 |
| operational | dc_raw     |          10 |     1.2745 |   0.7316 |   0.2675 |
| operational | market     |          10 |     1.0178 |   0.6132 |   0.2018 |
| preseason   | production |          10 |     1.1473 |   0.6927 |   0.2425 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 60 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          60 |     1.4538 |   0.6227 |   0.2057 |
| operational | dc_raw     |          60 |     1.0984 |   0.632  |   0.2137 |
| operational | market     |          60 |     1.0454 |   0.6305 |   0.2053 |
| preseason   | production |          60 |     1.0647 |   0.6376 |   0.2125 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Coventry City     | Newcastle United       | home_win        |                                    0.1709 |
| Manchester United | Tottenham Hotspur      | draw            |                                    0.2386 |
| Ipswich Town      | Fulham                 | home_win        |                                    0.2459 |
| Aston Villa       | Brentford              | draw            |                                    0.2625 |
| Hull City         | Everton                | draw            |                                    0.3599 |
| Crystal Palace    | Nottingham Forest      | home_win        |                                    0.3753 |
| Sunderland        | Brighton & Hove Albion | away_win        |                                    0.388  |
| Liverpool         | Manchester City        | away_win        |                                    0.404  |
| Chelsea           | AFC Bournemouth        | home_win        |                                    0.4681 |
| Arsenal           | Leeds United           | home_win        |                                    0.6667 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
