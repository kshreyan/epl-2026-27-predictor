# NHL Model Selection Report

Real rolling-origin backtest on 6515 real historical games (2021-10-12 to 2026-04-17, refit every 15 real games using only data strictly before that point -- no future leakage). Candidates compared honestly, not assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-victory regression), a plain Elo-only win-probability baseline, and a flat/home-field-only baseline. A fourth real candidate, Dixon-Coles (src/models/scoreline_models.py, reused as-is), is also compared here since this sport's real scoring is low/discrete like soccer's, unlike NFL/NBA/NCAA Football -- not assumed to win, same empirical discipline as every other candidate.

## Model comparison (lower log loss / Brier / RPS is better)

| model                                        |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:---------------------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only win probability                     |        6515 |   0.676569 |      0.483103 |                   0.241552 |
| Point-margin model (Elo + margin regression) |        6515 |   0.682367 |      0.489286 |                   0.244643 |
| Flat/home-field-only baseline                |        6515 |   0.691074 |      0.497921 |                   0.248961 |
| Dixon-Coles (real scoreline grid)            |        6515 |   0.829383 |      0.50914  |                   0.244367 |

## Selected model

**Elo-only win probability** has the lowest backtest log loss (0.6766) and is used as the primary model for 2026-27 predictions.

## Real historical margin-of-victory distribution (absolute, points)

| Percentile | Absolute margin (points) |
|---|---|
| 50th | 2.0 |
| 60th | 3.0 |
| 70th | 3.0 |
| 75th | 3.0 |
| 80th | 3.0 |
| 85th | 4.0 |
| 90th | 4.0 |

Used directly by compute_margin_survival_team_sport.py to set this league's real +2-Margin-Survival-equivalent threshold -- see that module's docstring for the exact choice and why.

## Limitations

- Sample size is far smaller than this project's own 500-match isotonic-calibration minimum is meant for, but close to or above it for both sports (unlike the thin-sample UEFA club competitions) -- raw model probabilities are still used uncalibrated here for consistency with every other league in this project; calibration is a real, separate future improvement, not assumed to be unnecessary.
- No historical market-odds source is wired in for either sport yet -- real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Point-margin model ratings are held fixed between real games within this backtest's own refit cadence (every 15 games) -- a team's rating does not update mid-chunk, the same simplification the domestic soccer backtest makes between its own refit boundaries.
