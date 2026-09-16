# LA_LIGA Matchweek 2 Update Report

Generated: 2026-09-16T07:27:44+00:00

Locked 10 real result(s). 326 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona   |                    0.06714 |                    0.00676 |                         0       |
| Málaga CF      |                    0.02636 |                    0.09763 |                         0.05182 |
| RC Deportivo   |                    0.02616 |                    0.09703 |                         0.04837 |
| R. Racing Club |                    0.02337 |                    0.08831 |                         0.08366 |
| Real Betis     |                    0.00334 |                    0.07656 |                        -0.00532 |
| Sevilla FC     |                    0.00038 |                    0.03218 |                        -0.08025 |
| Getafe CF      |                   -2e-05   |                    0.00117 |                        -0.07245 |
| Levante UD     |                   -0.00012 |                   -0.00104 |                        -0.0744  |
| Valencia CF    |                   -0.00032 |                   -0.01295 |                        -0.01644 |
| Rayo Vallecano |                   -0.00035 |                   -0.0141  |                        -0.01184 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
