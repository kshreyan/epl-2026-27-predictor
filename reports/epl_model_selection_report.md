# EPL Model Selection Report (Phase 1 preliminary)

Rolling-origin backtest, validation seasons 2019-20 to 2025-26, refit approximately every matchweek (10-match chronological chunks), predicting only with data strictly before each chunk. 2660 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |   accuracy |   favorite_accuracy |   draw_calibration_bias |   expected_calibration_error |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|-----------:|--------------------:|------------------------:|-----------------------------:|
| Dixon-Coles (main model)       |        2660 |     0.9856 |        0.5861 |                     0.2038 |     0.5259 |              0.6383 |                 -0.0005 |                          nan |
| Elo-only baseline              |        2660 |     0.9977 |        0.5941 |                     0.207  |     0.5263 |              0.6233 |                 -0.0185 |                          nan |
| Previous-season-table baseline |        2660 |     1.21   |        0.6777 |                     0.2342 |     0.4647 |              0.5667 |                 -0.1059 |                          nan |
| Simple Poisson baseline        |        2660 |     1.0178 |        0.6082 |                     0.2146 |     0.4962 |              0.6566 |                 -0.0007 |                          nan |

## Scoreline accuracy (Dixon-Coles)

| model                    |   n_matches |   exact_score_accuracy |   top_3_scoreline_hit_rate |   top_5_scoreline_hit_rate |   goal_mae |   total_goals_mae |
|:-------------------------|------------:|-----------------------:|---------------------------:|---------------------------:|-----------:|------------------:|
| Dixon-Coles (main model) |        2660 |                 0.1124 |                     0.3064 |                     0.4658 |     0.9472 |            1.4816 |

## Selected model

**Dixon-Coles (main model)** has the lowest backtest log loss (0.9856) and is used as the primary model for 2026-27 predictions. Promoted-team Elo offset used: -97.2 points, derived from 33 real historical promotion events.

## Limitations

- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not every single match, for compute-time reasons; within a chunk, later matches technically use a snapshot fit before the chunk first match rather than immediately before their own kickoff.
- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).
- No market-odds baseline is included in this comparison (no historical odds source with sufficient coverage was integrated in Phase 1).
- The promoted-team Elo/Dixon-Coles offset is a single global constant derived from the full historical dataset (including seasons after a given backtest validation point) -- a mild form of hyperparameter-level leakage, and the backtest itself does not apply the Dixon-Coles promoted-team adjustment (see reports/epl_2026_27_model_report.md).
