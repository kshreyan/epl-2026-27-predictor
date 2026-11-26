# EPL Matchweek 11 Update Report

Generated: 2026-11-25T19:57:55+00:00

Locked 10 real result(s). 270 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Brentford              |                    0.00274 |                    0.07251 |                        -0.00401 |
| Brighton & Hove Albion |                    0.00094 |                   -0.00656 |                         1e-05   |
| Liverpool              |                    0.00084 |                   -0.00638 |                         1e-05   |
| Manchester City        |                    0.00066 |                   -0.00793 |                         0       |
| Leeds United           |                    0.00033 |                   -0.0027  |                        -0.00052 |
| AFC Bournemouth        |                    9e-05   |                   -0.00688 |                        -0.00017 |
| Aston Villa            |                    3e-05   |                   -0.00229 |                        -0.00038 |
| Newcastle United       |                    2e-05   |                   -0.00337 |                         3e-05   |
| Tottenham Hotspur      |                    2e-05   |                   -0.00118 |                        -0.00099 |
| Nottingham Forest      |                    1e-05   |                   -0.00071 |                        -0.00394 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.0587 |   0.6531 |   0.222  |
| operational | dc_raw     |          10 |     1.0962 |   0.6769 |   0.2294 |
| operational | market     |          10 |     1.1381 |   0.7013 |   0.2368 |
| preseason   | production |          10 |     1.0595 |   0.6528 |   0.2216 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 110 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |         110 |     1.243  |   0.6087 |   0.2087 |
| operational | dc_raw     |         110 |     1.0557 |   0.6188 |   0.2149 |
| operational | market     |         110 |     1.0215 |   0.6132 |   0.2082 |
| preseason   | production |         110 |     1.0365 |   0.6223 |   0.2136 |
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
| Brentford         | Everton                | home_win        |                                    0.4608 |
| AFC Bournemouth   | Nottingham Forest      | home_win        |                                    0.4608 |
| Liverpool         | Manchester United      | home_win        |                                    0.5282 |
| Tottenham Hotspur | Ipswich Town           | home_win        |                                    0.6628 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
