# NBA Model Selection Report

Real rolling-origin backtest on 6108 real historical games (2021-10-19 to 2026-04-13, refit every 15 real games using only data strictly before that point -- no future leakage). Candidates compared honestly, not assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-victory regression, NOT soccer's Dixon-Coles/Poisson scoreline grid, which does not fit this sport's scoring scale), a plain Elo-only win-probability baseline, and a flat/home-field-only baseline.

## Model comparison (lower log loss / Brier / RPS is better)

| model                                        |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:---------------------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only win probability                     |        6108 |   0.637491 |      0.445356 |                   0.222678 |
| Point-margin model (Elo + margin regression) |        6108 |   0.662271 |      0.469571 |                   0.234786 |
| Flat/home-field-only baseline                |        6108 |   0.687817 |      0.494676 |                   0.247338 |

## Selected model

**Elo-only win probability** has the lowest backtest log loss (0.6375) and is used as the primary model for 2026-27 predictions.

## Real historical margin-of-victory distribution (absolute, points)

| Percentile | Absolute margin (points) |
|---|---|
| 50th | 10.0 |
| 60th | 12.0 |
| 70th | 15.0 |
| 75th | 17.0 |
| 80th | 19.0 |
| 85th | 22.0 |
| 90th | 25.0 |

Used directly by compute_margin_survival_team_sport.py to set this league's real +2-Margin-Survival-equivalent threshold -- see that module's docstring for the exact choice and why.

## Limitations

- Sample size is far smaller than this project's own 500-match isotonic-calibration minimum is meant for, but close to or above it for both sports (unlike the thin-sample UEFA club competitions) -- raw model probabilities are still used uncalibrated here for consistency with every other league in this project; calibration is a real, separate future improvement, not assumed to be unnecessary.
- No historical market-odds source is wired in for either sport yet -- real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Point-margin model ratings are held fixed between real games within this backtest's own refit cadence (every 15 games) -- a team's rating does not update mid-chunk, the same simplification the domestic soccer backtest makes between its own refit boundaries.
