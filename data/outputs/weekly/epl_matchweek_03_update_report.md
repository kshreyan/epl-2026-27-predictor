# EPL Matchweek 3 Update Report

Generated: 2026-09-10T10:07:37+00:00

Locked 10 real result(s). 350 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team              |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:------------------|---------------------------:|---------------------------:|--------------------------------:|
| Arsenal           |                    0.03042 |                    0.01533 |                         0       |
| Liverpool         |                    0.00364 |                    0.06159 |                        -0.00165 |
| Hull City         |                    0.00147 |                    0.00674 |                         0.01043 |
| Ipswich Town      |                    0.00086 |                    0.00343 |                         0.02922 |
| Coventry City     |                    0.00076 |                    0.00571 |                         0.01534 |
| Crystal Palace    |                    0.0001  |                    0.01123 |                        -0.0818  |
| Tottenham Hotspur |                   -3e-05   |                    0.00042 |                        -0.00879 |
| Sunderland        |                   -5e-05   |                    0.00226 |                        -0.01856 |
| Fulham            |                   -0.00033 |                   -0.01035 |                         0.05417 |
| Everton           |                   -0.00034 |                   -0.00401 |                        -0.0019  |

## Scoring

Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 was tagged); **operational** is the model's latest pre-kickoff prediction at any point in the season.

This matchweek (10 scored match(es)):

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          10 |     1.0128 |   0.6103 |   0.1352 |
| operational | dc_raw     |          10 |     0.9743 |   0.6005 |   0.136  |
| operational | market     |          10 |     1.0548 |   0.6415 |   0.1466 |
| preseason   | production |          10 |     1.0201 |   0.611  |   0.1371 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

Cumulative, all 30 real match(es) scored so far this season:

| track       | model      |   n_matches |   log_loss |    brier |      rps |
|:------------|:-----------|------------:|-----------:|---------:|---------:|
| operational | production |          30 |     0.9581 |   0.5683 |   0.1745 |
| operational | dc_raw     |          30 |     0.9506 |   0.5667 |   0.1762 |
| operational | market     |          30 |     1.0078 |   0.601  |   0.1889 |
| preseason   | production |          30 |     1.0104 |   0.601  |   0.1915 |
| preseason   | dc_raw     |           0 |   nan      | nan      | nan      |
| preseason   | market     |           0 |   nan      | nan      | nan      |

'production' is what the pipeline actually predicted (calibrated Dixon-Coles, or the ensemble on the seasons it's statistically justified, or a promoted challenger); 'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).

## Most surprising results

Matches where the actual outcome sat furthest into the model's predicted tail (lowest probability assigned to what actually happened):

| home_team              | away_team         | actual_result   |   predicted_probability_of_actual_outcome |
|:-----------------------|:------------------|:----------------|------------------------------------------:|
| Brentford              | Sunderland        | draw            |                                    0.2526 |
| Newcastle United       | AFC Bournemouth   | draw            |                                    0.2579 |
| Brighton & Hove Albion | Leeds United      | draw            |                                    0.2589 |
| Nottingham Forest      | Tottenham Hotspur | draw            |                                    0.2685 |
| Everton                | Manchester United | draw            |                                    0.2806 |
| Hull City              | Aston Villa       | draw            |                                    0.2909 |
| Fulham                 | Crystal Palace    | away_win        |                                    0.291  |
| Arsenal                | Chelsea           | home_win        |                                    0.5906 |
| Ipswich Town           | Liverpool         | away_win        |                                    0.7093 |
| Manchester City        | Coventry City     | home_win        |                                    0.8861 |

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
