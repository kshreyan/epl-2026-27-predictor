# SERIE_A Matchweek 4 Update Report

Generated: 2026-09-16T19:11:56+00:00

Locked 10 real result(s). 340 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Roma           |                    0.03592 |                    0.06732 |                         0       |
| Internazionale |                    0.01342 |                    0.01515 |                         0       |
| Como           |                    0.00485 |                    0.04819 |                        -2e-05   |
| Napoli         |                    0.00441 |                    0.07416 |                        -0.00015 |
| Sassuolo       |                    0.00053 |                    0.01692 |                        -0.02728 |
| Cagliari       |                    0.0001  |                    0.00958 |                        -0.03736 |
| Parma          |                    0       |                   -7e-05   |                         0.01398 |
| Lecce          |                    0       |                    0.00017 |                        -0.09819 |
| Monza          |                    0       |                   -0.00017 |                         0.06797 |
| Genoa          |                   -1e-05   |                   -0.00056 |                         0.01428 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
