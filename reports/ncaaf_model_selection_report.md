# NCAA Football Model Selection Report

Real rolling-origin backtest on 3680 real historical games (2021-08-28 to 2025-12-13, refit every 15 real games using only data strictly before that point -- no future leakage). Candidates compared honestly, not assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-victory regression), a plain Elo-only win-probability baseline, and a flat/home-field-only baseline. Soccer's Dixon-Coles/Poisson scoreline grid is NOT a candidate here -- it does not fit this sport's real scoring scale (confirmed directly, same reasoning as NFL/NBA). A real conference-aware variant of the point-margin model is also compared (season-reversion toward each team's own real conference mean -- see elo_model.run_elo's team_group docstring -- instead of the full real league-wide mean), since this sport's real strength gap between conferences (e.g. the SEC vs. a Group of 5 conference) is large and persistent -- never assumed to beat the flat-reversion version.

## Model comparison (lower log loss / Brier / RPS is better)

| model                                           |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:------------------------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only win probability                        |        3680 |   0.592331 |      0.406431 |                   0.203215 |
| Point-margin model (conference-aware reversion) |        3680 |   0.658275 |      0.465869 |                   0.232935 |
| Point-margin model (Elo + margin regression)    |        3680 |   0.660866 |      0.468357 |                   0.234179 |
| Flat/home-field-only baseline                   |        3680 |   0.679909 |      0.486794 |                   0.243397 |

## Selected model

**Elo-only win probability** has the lowest backtest log loss (0.5923) and is used as the primary model for 2026-27 predictions.

## Real historical margin-of-victory distribution (absolute, points)

| Percentile | Absolute margin (points) |
|---|---|
| 50th | 14.0 |
| 60th | 17.0 |
| 70th | 21.0 |
| 75th | 24.0 |
| 80th | 27.2 |
| 85th | 31.0 |
| 90th | 35.0 |

Used directly by compute_margin_survival_team_sport.py to set this league's real +2-Margin-Survival-equivalent threshold -- see that module's docstring for the exact choice and why.

## Limitations

- Sample size is far smaller than this project's own 500-match isotonic-calibration minimum is meant for, but close to or above it for both sports (unlike the thin-sample UEFA club competitions) -- raw model probabilities are still used uncalibrated here for consistency with every other league in this project; calibration is a real, separate future improvement, not assumed to be unnecessary.
- No historical market-odds source is wired in for either sport yet -- real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Point-margin model ratings are held fixed between real games within this backtest's own refit cadence (every 15 games) -- a team's rating does not update mid-chunk, the same simplification the domestic soccer backtest makes between its own refit boundaries.
