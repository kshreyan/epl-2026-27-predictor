# EPL Model Selection Report (Phase 1 preliminary)

Rolling-origin backtest, validation seasons 2019-20 to 2025-26, refit approximately every matchweek (10-match chronological chunks), predicting only with data strictly before each chunk. 2660 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |   accuracy |   favorite_accuracy |   draw_calibration_bias | expected_calibration_error   |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|-----------:|--------------------:|------------------------:|:-----------------------------|
| Dixon-Coles (main model)       |        2660 |     0.9865 |        0.5864 |                     0.2035 |     0.5289 |              0.6372 |                 -0.0089 |                              |
| Elo-only baseline              |        2660 |     0.9931 |        0.5912 |                     0.2055 |     0.5305 |              0.6075 |                 -0.0213 |                              |
| Previous-season-table baseline |        2660 |     1.21   |        0.6777 |                     0.2342 |     0.4647 |              0.5667 |                 -0.1059 |                              |
| Simple Poisson baseline        |        2660 |     1.0178 |        0.6082 |                     0.2146 |     0.4962 |              0.6566 |                 -0.0007 |                              |

## Scoreline accuracy (Dixon-Coles)

| model                    |   n_matches |   exact_score_accuracy |   top_3_scoreline_hit_rate |   top_5_scoreline_hit_rate |   goal_mae |   total_goals_mae |
|:-------------------------|------------:|-----------------------:|---------------------------:|---------------------------:|-----------:|------------------:|
| Dixon-Coles (main model) |        2660 |                  0.112 |                     0.3011 |                     0.4647 |     0.9436 |            1.4805 |

## Selected model

**Dixon-Coles (main model)** has the lowest backtest log loss (0.9865) and is used as the primary model for 2026-27 predictions. Promoted-team Elo offset used: -97.3 points, derived from 33 real historical promotion events.

## Limitations

- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not every single match, for compute-time reasons; within a chunk, later matches technically use a snapshot fit before the chunk's first match rather than immediately before their own kickoff.
- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).
- No market-odds baseline is included in this comparison (no historical odds source with sufficient coverage was integrated in Phase 1).
- The Dixon-Coles promoted-team offset is now leakage-safe (computed per validation season from only earlier real promotion events, and applied to that season's actual promoted clubs during backtest prediction). The **Elo** promoted-team offset is still a single global constant computed from the full historical dataset -- a smaller, documented remaining gap.
