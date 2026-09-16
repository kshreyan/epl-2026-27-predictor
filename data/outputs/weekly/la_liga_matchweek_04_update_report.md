# LA_LIGA Matchweek 4 Update Report

Generated: 2026-09-16T07:29:12+00:00

Locked 10 real result(s). 326 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team             |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Barcelona     |                    0.12782 |                    0.00371 |                         0       |
| Real Betis       |                    0.00152 |                    0.1038  |                        -0.00336 |
| Athletic Club    |                    0.00032 |                    0.07581 |                        -0.02793 |
| Deportivo Alavés |                    0.0002  |                    0.05638 |                        -0.03291 |
| Rayo Vallecano   |                    4e-05   |                    0.01293 |                        -0.05225 |
| Real Sociedad    |                    4e-05   |                    0.03528 |                        -0.02701 |
| Málaga CF        |                    2e-05   |                    0.00101 |                        -0.01034 |
| RC Deportivo     |                    2e-05   |                    0.00709 |                        -0.09204 |
| R. Racing Club   |                   -1e-05   |                    9e-05   |                         0.02535 |
| Elche CF         |                   -1e-05   |                   -0.00478 |                         0.04932 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
