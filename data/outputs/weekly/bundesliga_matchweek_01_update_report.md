# BUNDESLIGA Matchweek 1 Update Report

Generated: 2026-09-16T20:09:12+00:00

Locked 9 real result(s). 297 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| FC Bayern München   |                    0.03795 |                    0.00332 |                         0       |
| RB Leipzig          |                    0.00282 |                    0.10295 |                        -0.00235 |
| Sport-Club Freiburg |                    0.00021 |                    0.03938 |                        -0.03374 |
| SV Elversberg       |                    0.00019 |                    0.01342 |                        -0.08968 |
| 1. FC Köln          |                    4e-05   |                    0.01273 |                        -0.06771 |
| FC Augsburg         |                    4e-05   |                    0.01097 |                        -0.05162 |
| SC Paderborn 07     |                    2e-05   |                    0.00623 |                        -0.01915 |
| FC Schalke 04       |                   -2e-05   |                    0.00334 |                         0.02223 |
| SV Werder Bremen    |                   -7e-05   |                   -0.00807 |                         0.09479 |
| 1. FC Union Berlin  |                   -8e-05   |                   -0.00142 |                         0.00757 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
