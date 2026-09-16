# LIGUE_1 Matchweek 2 Update Report

Generated: 2026-09-16T23:44:54+00:00

Locked 9 real result(s). 288 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                 |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:---------------------|---------------------------:|---------------------------:|--------------------------------:|
| AS Monaco            |                    0.03281 |                    0.10956 |                        -0.00552 |
| Paris FC             |                    0.01596 |                    0.09026 |                        -0.04868 |
| RC Strasbourg Alsace |                    0.00828 |                    0.05684 |                        -0.02147 |
| LOSC Lille           |                    0.00642 |                    0.01748 |                        -0.00037 |
| Stade Rennais FC     |                    0.00594 |                    0.02336 |                        -0.00424 |
| Paris Saint-Germain  |                    0.00212 |                   -0.00352 |                         1e-05   |
| Estac Troyes         |                    0.00032 |                    0.00491 |                        -0.05736 |
| Toulouse FC          |                    0.00019 |                   -0.0035  |                         0.00358 |
| Angers SCO           |                    0.0001  |                    0.00323 |                        -0.16781 |
| Havre Athletic Club  |                    3e-05   |                    0.00119 |                        -0.02758 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
