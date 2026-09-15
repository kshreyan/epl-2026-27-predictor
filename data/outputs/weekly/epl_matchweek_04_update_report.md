# EPL Matchweek 4 Update Report

Generated: 2026-09-15T02:23:16+00:00

Locked 10 real result(s). 340 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal                |                    0.02352 |                    0.0144  |                         0       |
| Manchester City        |                    0.01163 |                    0.02133 |                        -2e-05   |
| Leeds United           |                    0.00275 |                    0.09165 |                        -0.04546 |
| Brighton & Hove Albion |                    0.00268 |                    0.09816 |                        -0.01537 |
| Nottingham Forest      |                    0.00053 |                    0.03779 |                        -0.0423  |
| Fulham                 |                    2e-05   |                    0.00191 |                        -0.04908 |
| Tottenham Hotspur      |                   -7e-05   |                   -0.00216 |                        -0.02297 |
| Crystal Palace         |                   -0.00027 |                   -0.01206 |                         0.04498 |
| Everton                |                   -0.00066 |                   -0.00428 |                        -0.00934 |
| Sunderland             |                   -0.00089 |                   -0.0131  |                         0.01171 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.1046 |   0.6731 |   0.2095 |
| operational | dc_raw     |          10 |     1.1093 |   0.665  |   0.2161 |
| operational | market     |          10 |     1.1712 |   0.7305 |   0.2227 |
| preseason   | production |          10 |     1.208  |   0.7407 |   0.2411 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 40 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          40 |     0.9947 |   0.5945 |   0.1833 |
| operational | dc_raw     |          40 |     0.9903 |   0.5913 |   0.1862 |
| operational | market     |          40 |     1.0487 |   0.6334 |   0.1974 |
| preseason   | production |          40 |     1.0598 |   0.6359 |   0.2039 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Crystal Palace    | Ipswich Town           | away_win        |                                    0.1633 |
| Liverpool         | Fulham                 | draw            |                                    0.2166 |
| AFC Bournemouth   | Brentford              | draw            |                                    0.2589 |
| Tottenham Hotspur | Everton                | draw            |                                    0.2714 |
| Aston Villa       | Nottingham Forest      | away_win        |                                    0.3081 |
| Chelsea           | Hull City              | draw            |                                    0.325  |
| Leeds United      | Newcastle United       | home_win        |                                    0.3964 |
| Manchester United | Manchester City        | away_win        |                                    0.4571 |
| Coventry City     | Brighton & Hove Albion | away_win        |                                    0.5946 |
| Sunderland        | Arsenal                | away_win        |                                    0.5951 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
