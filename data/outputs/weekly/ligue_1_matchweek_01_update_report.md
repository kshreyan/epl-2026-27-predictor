# LIGUE_1 Matchweek 1 Update Report

Generated: 2026-09-16T23:44:30+00:00

Locked 9 real result(s). 297 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team                   |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:-----------------------|---------------------------:|---------------------------:|--------------------------------:|
| Olympique de Marseille |                    0.03426 |                    0.10074 |                        -0.0074  |
| RC Lens                |                    0.03341 |                    0.05452 |                        -0.00272 |
| Olympique Lyonnais     |                    0.02186 |                    0.07513 |                        -0.00993 |
| LOSC Lille             |                    0.01922 |                    0.05131 |                        -0.00584 |
| AS Monaco              |                    0.00807 |                    0.02779 |                        -0.00875 |
| Estac Troyes           |                    0.0004  |                    0.00282 |                        -0.07026 |
| Le Mans FC             |                    0.00036 |                    0.00269 |                        -0.06376 |
| Angers SCO             |                   -9e-05   |                   -0.00259 |                         0.06165 |
| Havre Athletic Club    |                   -0.00027 |                   -0.00793 |                         0.04389 |
| Stade Brestois 29      |                   -0.00075 |                   -0.01211 |                        -0.00833 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
