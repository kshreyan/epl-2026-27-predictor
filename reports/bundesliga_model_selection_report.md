# Bundesliga Model Selection Report (Phase 1 preliminary)

Rolling-origin backtest, validation seasons 2019-20 to 2025-26, refit approximately every matchweek (10-match chronological chunks), predicting only with data strictly before each chunk. 2142 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |   accuracy |   favorite_accuracy |   draw_calibration_bias | expected_calibration_error   |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|-----------:|--------------------:|------------------------:|:-----------------------------|
| Dixon-Coles (main model)       |        2142 |     1.0026 |        0.5976 |                     0.2056 |     0.5145 |              0.6216 |                 -0.0068 |                              |
| Elo-only baseline              |        2142 |     1.0062 |        0.6005 |                     0.207  |     0.5112 |              0.595  |                 -0.0315 |                              |
| Previous-season-table baseline |        2142 |     1.2307 |        0.6823 |                     0.2322 |     0.4781 |              0.577  |                 -0.1324 |                              |
| Simple Poisson baseline        |        2142 |     1.0177 |        0.6074 |                     0.2109 |     0.5005 |              0.6842 |                 -0.0222 |                              |

## Scoreline accuracy (Dixon-Coles)

| model                    |   n_matches |   exact_score_accuracy |   top_3_scoreline_hit_rate |   top_5_scoreline_hit_rate |   goal_mae |   total_goals_mae |
|:-------------------------|------------:|-----------------------:|---------------------------:|---------------------------:|-----------:|------------------:|
| Dixon-Coles (main model) |        2142 |                 0.1139 |                     0.2782 |                     0.4164 |     0.9956 |            1.5532 |

## Selected model

**Dixon-Coles (main model)** has the lowest backtest log loss (1.0026) and is used as the primary model for 2026-27 predictions. Promoted-team Elo offset used: -63.0 points, derived from 23 real historical promotion events.

## Limitations

- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not every single match, for compute-time reasons; within a chunk, later matches technically use a snapshot fit before the chunk's first match rather than immediately before their own kickoff.
- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).
- No market-odds baseline is included in this comparison (no historical odds source with sufficient coverage was integrated in Phase 1).
- The Dixon-Coles promoted-team offset is now leakage-safe (computed per validation season from only earlier real promotion events, and applied to that season's actual promoted clubs during backtest prediction). The **Elo** promoted-team offset is still a single global constant computed from the full historical dataset -- a smaller, documented remaining gap.
