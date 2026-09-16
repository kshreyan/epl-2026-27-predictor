# LA_LIGA Matchweek 3 Update Report

Generated: 2026-09-16T07:28:29+00:00

Locked 10 real result(s). 326 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona              |                    0.05329 |                    0.01056 |                         0       |
| Real Madrid               |                    0.0349  |                    0.05648 |                        -1e-05   |
| Atlético de Madrid        |                    0.009   |                    0.16176 |                        -0.00048 |
| CA Osasuna                |                    0.00032 |                    0.04514 |                        -0.01507 |
| Levante UD                |                    0.00026 |                    0.04438 |                        -0.08576 |
| Athletic Club             |                    0.00026 |                    0.04927 |                        -0.03279 |
| Deportivo Alavés          |                    7e-05   |                    0.02913 |                        -0.02481 |
| Real Sociedad             |                    5e-05   |                    0.02716 |                        -0.02091 |
| RCD Espanyol de Barcelona |                   -2e-05   |                   -0.00251 |                         0.04499 |
| Elche CF                  |                   -5e-05   |                    0.00049 |                         0.05283 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
