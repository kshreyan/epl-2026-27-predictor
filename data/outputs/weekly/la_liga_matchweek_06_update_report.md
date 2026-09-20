# LA_LIGA Matchweek 6 Update Report

Generated: 2026-09-20T23:46:02+00:00

Locked 9 real result(s). 321 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team           |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona   |                          0 |                          0 |                               0 |
| Real Madrid    |                          0 |                          0 |                               0 |
| R. Racing Club |                          0 |                          0 |                               0 |
| RC Deportivo   |                          0 |                          0 |                               0 |
| Elche CF       |                          0 |                          0 |                               0 |
| Getafe CF      |                          0 |                          0 |                               0 |
| Valencia CF    |                          0 |                          0 |                               0 |
| CA Osasuna     |                          0 |                          0 |                               0 |
| Levante UD     |                          0 |                          0 |                               0 |
| Celta Vigo     |                          0 |                          0 |                               0 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
