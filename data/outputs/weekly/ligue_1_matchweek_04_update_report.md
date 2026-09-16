# LIGUE_1 Matchweek 4 Update Report

Generated: 2026-09-16T23:45:39+00:00

Locked 9 real result(s). 270 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| Paris Saint-Germain |                    0.05547 |                    0.03724 |                        -4e-05   |
| Stade Rennais FC    |                    0.01578 |                    0.08812 |                        -0.00499 |
| LOSC Lille          |                    0.01253 |                    0.0511  |                        -0.00086 |
| AJ Auxerre          |                    0.00011 |                    0.00336 |                        -0.08939 |
| Angers SCO          |                    0       |                   -0.00056 |                        -0.00863 |
| Havre Athletic Club |                   -8e-05   |                   -0.00113 |                         0.02788 |
| Le Mans FC          |                   -0.00026 |                   -0.00248 |                         0.00053 |
| OGC Nice            |                   -0.00035 |                   -0.00493 |                         0.05164 |
| Toulouse FC         |                   -0.00036 |                   -0.00209 |                        -0.0122  |
| Estac Troyes        |                   -0.00045 |                   -0.00428 |                         0.0317  |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
