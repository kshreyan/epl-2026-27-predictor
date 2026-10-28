# NFL Model Selection Report

Real rolling-origin backtest on 1314 real historical games (2021-09-09 to 2026-01-04, refit every 15 real games using only data strictly before that point -- no future leakage). Candidates compared honestly, not assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-victory regression), a plain Elo-only win-probability baseline, and a flat/home-field-only baseline. Soccer's Dixon-Coles/Poisson scoreline grid is NOT a candidate here -- it does not fit this sport's real scoring scale (confirmed directly, same reasoning as NFL/NBA).

## Model comparison (lower log loss / Brier / RPS is better)

| model                                        |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:---------------------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Point-margin model (Elo + margin regression) |        1314 |   0.720375 |      0.494597 |                   0.245481 |
| Flat/home-field-only baseline                |        1314 |   0.725868 |      0.500176 |                   0.248566 |
| Elo-only win probability                     |        1314 |   0.897447 |      0.529577 |                   0.240052 |

## Selected model

**Point-margin model (Elo + margin regression)** has the lowest backtest log loss (0.7204) and is used as the primary model for 2026-27 predictions.

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
