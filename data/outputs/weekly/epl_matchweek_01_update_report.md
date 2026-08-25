# EPL Matchweek 1 Update Report

Generated: 2026-08-25T19:05:05+00:00

Locked 10 real result(s). 370 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Manchester City        |                    0.01316 |                    0.01426 |                         0       |
| Arsenal                |                    0.0115  |                    0.01222 |                         1e-05   |
| Brighton & Hove Albion |                    0.00814 |                    0.09578 |                        -0.01553 |
| Brentford              |                    0.00461 |                    0.05993 |                        -0.01126 |
| Chelsea                |                    0.00372 |                    0.05811 |                        -0.00664 |
| Leeds United           |                    0.00185 |                    0.03639 |                        -0.03688 |
| Everton                |                    0.00133 |                    0.0275  |                        -0.02257 |
| Ipswich Town           |                    0.00057 |                    0.00815 |                        -0.10309 |
| Hull City              |                    0.00046 |                    0.00881 |                        -0.11192 |
| Coventry City          |                    0.00026 |                    0.00543 |                        -0.04555 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.0083 |   0.5948 |   0.2412 |
| operational | dc_raw     |          10 |     1.0574 |   0.6216 |   0.2537 |
| operational | market     |          10 |     0.9792 |   0.5709 |   0.2303 |
| preseason   | production |          10 |     1.0599 |   0.6247 |   0.2549 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 10 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.0083 |   0.5948 |   0.2412 |
| operational | dc_raw     |          10 |     1.0574 |   0.6216 |   0.2537 |
| operational | market     |          10 |     0.9792 |   0.5709 |   0.2303 |
| preseason   | production |          10 |     1.0599 |   0.6247 |   0.2549 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team         | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:------------------|:----------------|------------------------------------------:|
| Hull City              | Manchester United | home_win        |                                    0.1598 |
| Ipswich Town           | Sunderland        | home_win        |                                    0.2322 |
| Newcastle United       | Liverpool         | draw            |                                    0.2506 |
| Nottingham Forest      | Leeds United      | away_win        |                                    0.2925 |
| Fulham                 | Chelsea           | away_win        |                                    0.414  |
| Brighton & Hove Albion | Aston Villa       | home_win        |                                    0.4168 |
| Everton                | Crystal Palace    | home_win        |                                    0.4265 |
| Brentford              | Tottenham Hotspur | home_win        |                                    0.4396 |
| Manchester City        | AFC Bournemouth   | home_win        |                                    0.6184 |
| Arsenal                | Coventry City     | home_win        |                                    0.7678 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury, lineup, and market-odds data remain unavailable (see config/data_sources.yaml) -- this update only incorporates real completed-match results and team-strength re-fitting.
