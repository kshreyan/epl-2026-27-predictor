# SERIE_A Matchweek 3 Update Report

Generated: 2026-09-16T19:11:25+00:00

Locked 10 real result(s). 350 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| Internazionale |                    0.03    |                    0.0223  |                         0       |
| Como           |                    0.02399 |                    0.09588 |                        -0.00016 |
| Roma           |                    0.02137 |                    0.06197 |                        -2e-05   |
| Lazio          |                    0.00136 |                    0.03371 |                        -0.00286 |
| Torino         |                    4e-05   |                    0.00166 |                        -0.07939 |
| Cagliari       |                    3e-05   |                    0.00167 |                        -0.0419  |
| Lecce          |                    0       |                   -0.00015 |                         0.04273 |
| Parma          |                   -2e-05   |                   -0.00039 |                         0.00931 |
| Genoa          |                   -6e-05   |                   -0.00214 |                         0.03489 |
| Sassuolo       |                   -0.00014 |                   -0.00198 |                        -0.01551 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
