# EPL Matchweek 2 Update Report

Generated: 2026-09-01T10:36:33+00:00

Locked 10 real result(s). 360 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team              |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:------------------|---------------------------:|---------------------------:|--------------------------------:|
| Manchester City   |                    0.02569 |                    0.03172 |                        -4e-05   |
| Arsenal           |                    0.01949 |                    0.02511 |                        -4e-05   |
| Hull City         |                    0.0021  |                    0.0202  |                        -0.06184 |
| Newcastle United  |                    0.00151 |                    0.05924 |                        -0.01312 |
| Ipswich Town      |                    0.00093 |                    0.01193 |                        -0.01017 |
| Coventry City     |                    0.00052 |                    0.00768 |                         0.00419 |
| Chelsea           |                    0.00018 |                    0.04821 |                        -0.0058  |
| Sunderland        |                    3e-05   |                    0.00995 |                        -0.0618  |
| Crystal Palace    |                   -0.00035 |                   -0.00965 |                         0.05137 |
| Nottingham Forest |                   -0.00036 |                    0.00304 |                        -0.01174 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     0.8533 |   0.4998 |   0.1471 |
| operational | dc_raw     |          10 |     0.82   |   0.4781 |   0.1389 |
| operational | market     |          10 |     0.9895 |   0.5906 |   0.1898 |
| preseason   | production |          10 |     0.9512 |   0.5672 |   0.1825 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 20 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          20 |     0.9308 |   0.5473 |   0.1942 |
| operational | dc_raw     |          20 |     0.9387 |   0.5499 |   0.1963 |
| operational | market     |          20 |     0.9843 |   0.5808 |   0.2101 |
| preseason   | production |          20 |     1.0055 |   0.5959 |   0.2187 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Liverpool         | Nottingham Forest      | draw            |                                    0.2397 |
| Leeds United      | Brentford              | draw            |                                    0.2679 |
| AFC Bournemouth   | Everton                | draw            |                                    0.2828 |
| Tottenham Hotspur | Newcastle United       | away_win        |                                    0.3462 |
| Sunderland        | Fulham                 | home_win        |                                    0.3911 |
| Chelsea           | Brighton & Hove Albion | home_win        |                                    0.4481 |
| Aston Villa       | Arsenal                | away_win        |                                    0.5706 |
| Crystal Palace    | Manchester City        | away_win        |                                    0.576  |
| Manchester United | Ipswich Town           | home_win        |                                    0.7262 |
| Coventry City     | Hull City              | away_win        |                                    0.7489 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
