# NFL Model Selection Report

Real rolling-origin backtest on 1329 real historical games (2021-09-10 to 2026-01-05, refit every 15 real games using only data strictly before that point -- no future leakage). Candidates compared honestly, not assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-victory regression, NOT soccer's Dixon-Coles/Poisson scoreline grid, which does not fit this sport's scoring scale), a plain Elo-only win-probability baseline, and a flat/home-field-only baseline.

## Model comparison (lower log loss / Brier / RPS is better)

| model                                        |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:---------------------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Point-margin model (Elo + margin regression) |        1329 |   0.701077 |      0.476258 |                   0.236329 |
| Flat/home-field-only baseline                |        1329 |   0.725639 |      0.50027  |                   0.24863  |
| Elo-only win probability                     |        1329 |   0.896264 |      0.528785 |                   0.239634 |

## Selected model

**Point-margin model (Elo + margin regression)** has the lowest backtest log loss (0.7011) and is used as the primary model for 2026-27 predictions.

## Real historical margin-of-victory distribution (absolute, points)

| Percentile | Absolute margin (points) |
|---|---|
| 50th | 8.0 |
| 60th | 10.0 |
| 70th | 14.0 |
| 75th | 17.0 |
| 80th | 18.4 |
| 85th | 21.0 |
| 90th | 24.0 |

Used directly by compute_margin_survival_team_sport.py to set this league's real +2-Margin-Survival-equivalent threshold -- see that module's docstring for the exact choice and why.

## Limitations

- Sample size is far smaller than this project's own 500-match isotonic-calibration minimum is meant for, but close to or above it for both sports (unlike the thin-sample UEFA club competitions) -- raw model probabilities are still used uncalibrated here for consistency with every other league in this project; calibration is a real, separate future improvement, not assumed to be unnecessary.
- No historical market-odds source is wired in for either sport yet -- real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Point-margin model ratings are held fixed between real games within this backtest's own refit cadence (every 15 games) -- a team's rating does not update mid-chunk, the same simplification the domestic soccer backtest makes between its own refit boundaries.
