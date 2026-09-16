# SERIE_A Matchweek 2 Update Report

Generated: 2026-09-16T19:10:55+00:00

Locked 10 real result(s). 360 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:----------|---------------------------:|---------------------------:|--------------------------------:|
| Roma      |                    0.03399 |                    0.05837 |                        -7e-05   |
| Como      |                    0.01176 |                    0.05133 |                        -0.00032 |
| Juventus  |                    0.00997 |                    0.03921 |                        -0.00018 |
| Atalanta  |                    0.00337 |                    0.02204 |                        -0.00013 |
| Frosinone |                    0.00088 |                    0.00897 |                        -0.13975 |
| Venezia   |                    0.00048 |                    0.00523 |                        -0.06264 |
| Monza     |                    0.00044 |                    0.00585 |                        -0.04261 |
| Lazio     |                    0.00015 |                    0.00333 |                        -0.00309 |
| Udinese   |                    4e-05   |                    0.00132 |                        -0.01465 |
| Parma     |                    0       |                   -0.00134 |                         0.06061 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
