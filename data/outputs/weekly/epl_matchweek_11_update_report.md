# EPL Matchweek 11 Update Report

Generated: 2026-11-23T16:38:10+00:00

Locked 9 real result(s). 271 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team              |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:------------------|---------------------------:|---------------------------:|--------------------------------:|
| Liverpool         |                    0.03329 |                    0.11682 |                        -0.0001  |
| Arsenal           |                    0.00646 |                   -0.00257 |                         0       |
| AFC Bournemouth   |                    0.00246 |                    0.05685 |                        -0.00254 |
| Leeds United      |                    0.00193 |                    0.07244 |                        -0.01502 |
| Brentford         |                    0.00084 |                    0.01149 |                         0.00044 |
| Everton           |                    0.0002  |                    0.00371 |                         0.00304 |
| Tottenham Hotspur |                    5e-05   |                    0.00488 |                        -0.01962 |
| Hull City         |                    2e-05   |                    0.0008  |                        -0.09456 |
| Newcastle United  |                    1e-05   |                    0.00685 |                        -0.00514 |
| Sunderland        |                    0       |                   -0.00026 |                        -0.0085  |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (9 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |           9 |     1.0903 |   0.6772 |   0.2264 |
| operational | dc_raw     |           9 |     1.1348 |   0.7058 |   0.236  |
| operational | market     |           9 |     1.1749 |   0.7281 |   0.2416 |
| preseason   | production |           9 |     1.0869 |   0.6736 |   0.2246 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 109 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |         109 |     1.2473 |   0.6102 |   0.2089 |
| operational | dc_raw     |         109 |     1.0585 |   0.6206 |   0.2153 |
| operational | market     |         109 |     1.0235 |   0.6146 |   0.2083 |
| preseason   | production |         109 |     1.0386 |   0.6237 |   0.2138 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team         | away_team              | actual_result   |   predicted_probability_of_actual_outcome |
|:------------------|:-----------------------|:----------------|------------------------------------------:|
| Hull City         | Brighton & Hove Albion | home_win        |                                    0.2155 |
| Manchester City   | Fulham                 | draw            |                                    0.2511 |
| Newcastle United  | Arsenal                | draw            |                                    0.2687 |
| Chelsea           | Leeds United           | away_win        |                                    0.2695 |
| Aston Villa       | Sunderland             | draw            |                                    0.2769 |
| Coventry City     | Crystal Palace         | home_win        |                                    0.3128 |
| AFC Bournemouth   | Nottingham Forest      | home_win        |                                    0.4608 |
| Liverpool         | Manchester United      | home_win        |                                    0.5282 |
| Tottenham Hotspur | Ipswich Town           | home_win        |                                    0.6628 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
