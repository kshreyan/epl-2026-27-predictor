# EPL Matchweek 10 Update Report

Generated: 2026-11-09T14:30:24+00:00

Locked 10 real result(s). 280 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal                |                    0.07687 |                    0.00323 |                         0       |
| Brighton & Hove Albion |                    0.02633 |                    0.07801 |                        -3e-05   |
| Liverpool              |                    0.00995 |                    0.09189 |                        -0.00014 |
| AFC Bournemouth        |                    0.00037 |                    0.01842 |                        -0.0036  |
| Leeds United           |                    0.00014 |                    0.014   |                        -0.01587 |
| Everton                |                    0.00012 |                    0.00981 |                        -0.01195 |
| Nottingham Forest      |                    4e-05   |                    0.00641 |                        -0.07658 |
| Coventry City          |                    1e-05   |                   -0.0002  |                         0.04132 |
| Fulham                 |                    1e-05   |                   -0.00215 |                         0.00675 |
| Hull City              |                    0       |                   -0.00033 |                         0.02132 |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     0.9153 |   0.5314 |   0.1874 |
| operational | dc_raw     |          10 |     0.8995 |   0.5181 |   0.1817 |
| operational | market     |          10 |     0.9327 |   0.547  |   0.1959 |
| preseason   | production |          10 |     0.9137 |   0.5335 |   0.1862 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 100 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |         100 |     1.2614 |   0.6042 |   0.2074 |
| operational | dc_raw     |         100 |     1.0516 |   0.6129 |   0.2134 |
| operational | market     |         100 |     1.0099 |   0.6044 |   0.2053 |
| preseason   | production |         100 |     1.0342 |   0.6192 |   0.2128 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team         | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:------------------|:----------------|------------------------------------------:|
| Nottingham Forest      | Manchester City   | home_win        |                                    0.2161 |
| Manchester United      | Aston Villa       | draw            |                                    0.2568 |
| Fulham                 | Newcastle United  | draw            |                                    0.2577 |
| Sunderland             | Chelsea           | home_win        |                                    0.288  |
| Leeds United           | Tottenham Hotspur | home_win        |                                    0.3883 |
| Brighton & Hove Albion | Brentford         | home_win        |                                    0.491  |
| Crystal Palace         | Liverpool         | away_win        |                                    0.5395 |
| Everton                | Coventry City     | home_win        |                                    0.5677 |
| Ipswich Town           | AFC Bournemouth   | away_win        |                                    0.5873 |
| Arsenal                | Hull City         | home_win        |                                    0.7501 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
