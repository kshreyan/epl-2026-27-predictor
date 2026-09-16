# SERIE_A Matchweek 1 Update Report

Generated: 2026-09-16T19:10:25+00:00

Locked 10 real result(s). 370 fixtures remain to be predicted/simulated.

## Biggest title-probability movers

| team      |   title_probability_change |   top_4_probability_change |   relegation_probability_change |
|:----------|---------------------------:|---------------------------:|--------------------------------:|
| Roma      |                    0.04003 |                    0.09708 |                        -0.00027 |
| Napoli    |                    0.01429 |                    0.05135 |                        -0.00046 |
| Milan     |                    0.00257 |                    0.01711 |                        -0.00113 |
| Lazio     |                    0.00163 |                    0.02277 |                        -0.00928 |
| Atalanta  |                    0.00098 |                    0.00692 |                        -0.00048 |
| Cagliari  |                    6e-05   |                    0.00203 |                        -0.06557 |
| Frosinone |                    3e-05   |                    0.0002  |                         0.04839 |
| Monza     |                    3e-05   |                    0.00031 |                         0.03677 |
| Venezia   |                    2e-05   |                    0.00011 |                         0.07446 |
| Lecce     |                    0       |                    0.00071 |                        -0.14389 |

## Scoring

Not attempted -- this matchweek was locked as part of onboarding this league mid-season (its real matches were already played before this pipeline started predicting for it), so there is no honest pre-kickoff prediction to score it against.

## Recalibration gate

Not attempted this matchweek -- either fewer than 150 real completed matches exist yet, or this matchweek is not on the evaluation cadence (every 5th matchweek, recalibration_gate.py's EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No automatic weekly recalibration ever runs; this gate only activates on cadence, and only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin evaluations across the whole season so far.

## Data-quality warnings

- Injury and lineup data remain unavailable (see config/data_sources.yaml).
- Market-odds data is connected (ODDS_API_KEY) and feeds both the scoring baseline above and, for any fixture with real odds available, the model+market blend in live predictions -- see reports/epl_2026_27_model_report.md "Model+market blend". Most fixtures still have no real market posted this far from their own kickoff.
