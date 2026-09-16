# Ligue 1 Model Selection Report (Phase 1 preliminary)

Rolling-origin backtest, validation seasons 2019-20 to 2025-26, refit approximately every matchweek (10-match chronological chunks), predicting only with data strictly before each chunk. 2337 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |   accuracy |   favorite_accuracy |   draw_calibration_bias | expected_calibration_error   |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|-----------:|--------------------:|------------------------:|:-----------------------------|
| Dixon-Coles (main model)       |        2337 |     1.0108 |        0.604  |                     0.2095 |     0.5139 |              0.6081 |                 -0.0025 |                              |
| Elo-only baseline              |        2337 |     1.015  |        0.6065 |                     0.2103 |     0.5066 |              0.5819 |                 -0.03   |                              |
| Previous-season-table baseline |        2337 |     1.2211 |        0.6794 |                     0.2319 |     0.469  |              0.5424 |                 -0.1279 |                              |
| Simple Poisson baseline        |        2337 |     1.0239 |        0.6139 |                     0.2142 |     0.4959 |              0.6327 |                 -0.0019 |                              |

## Scoreline accuracy (Dixon-Coles)

| model                    |   n_matches |   exact_score_accuracy |   top_3_scoreline_hit_rate |   top_5_scoreline_hit_rate |   goal_mae |   total_goals_mae |
|:-------------------------|------------:|-----------------------:|---------------------------:|---------------------------:|-----------:|------------------:|
| Dixon-Coles (main model) |        2337 |                 0.1108 |                     0.3068 |                     0.4733 |     0.9465 |            1.4925 |

## Selected model

**Dixon-Coles (main model)** has the lowest backtest log loss (1.0108) and is used as the primary model for 2026-27 predictions. Promoted-team Elo offset used: -64.8 points, derived from 28 real historical promotion events.

## Limitations

- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not every single match, for compute-time reasons; within a chunk, later matches technically use a snapshot fit before the chunk's first match rather than immediately before their own kickoff.
- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).
- No market-odds baseline is included in this comparison (no historical odds source with sufficient coverage was integrated in Phase 1).
- The Dixon-Coles promoted-team offset is now leakage-safe (computed per validation season from only earlier real promotion events, and applied to that season's actual promoted clubs during backtest prediction). The **Elo** promoted-team offset is still a single global constant computed from the full historical dataset -- a smaller, documented remaining gap.
