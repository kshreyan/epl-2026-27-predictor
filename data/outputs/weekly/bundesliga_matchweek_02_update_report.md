# BUNDESLIGA Matchweek 2 Update Report

Generated: 2026-09-16T20:09:37+00:00

Locked 9 real result(s). 288 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:--------------------|---------------------------:|---------------------------:|--------------------------------:|
| Borussia Dortmund   |                    0.0286  |                   -0.00022 |                        -8e-05   |
| SV Elversberg       |                    0.01932 |                    0.08181 |                        -0.00894 |
| Bayer 04 Leverkusen |                    0.01573 |                    0.04818 |                        -0.00144 |
| FC Schalke 04       |                    0.01058 |                    0.06825 |                         0.00493 |
| SC Paderborn 07     |                    0.00997 |                    0.05871 |                         0.05894 |
| VfB Stuttgart       |                    0.00624 |                    0.02026 |                        -0.00296 |
| 1. FSV Mainz 05     |                    0.00131 |                    0.0536  |                        -0.05551 |
| Sport-Club Freiburg |                    0.00076 |                    0.01014 |                        -0.02405 |
| FC Augsburg         |                    0.00056 |                    0.03196 |                        -0.10261 |
| SV Werder Bremen    |                    5e-05   |                    0.00572 |                        -0.15207 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
