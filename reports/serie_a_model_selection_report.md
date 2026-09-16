# Serie A Model Selection Report (Phase 1 preliminary)

Rolling-origin backtest, validation seasons 2019-20 to 2025-26, refit approximately every matchweek (10-match chronological chunks), predicting only with data strictly before each chunk. 2660 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |   accuracy |   favorite_accuracy |   draw_calibration_bias | expected_calibration_error   |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|-----------:|--------------------:|------------------------:|:-----------------------------|
| Dixon-Coles (main model)       |        2660 |     0.9926 |        0.5908 |                     0.1991 |     0.532  |              0.6025 |                 -0.0206 |                              |
| Elo-only baseline              |        2660 |     1.0043 |        0.5984 |                     0.2016 |     0.5259 |              0.6016 |                 -0.0479 |                              |
| Previous-season-table baseline |        2660 |     1.2252 |        0.6773 |                     0.2263 |     0.4812 |              0.5606 |                 -0.1323 |                              |
| Simple Poisson baseline        |        2660 |     1.0002 |        0.5954 |                     0.2011 |     0.5169 |              0.6328 |                 -0.0365 |                              |

## Scoreline accuracy (Dixon-Coles)

| model                    |   n_matches |   exact_score_accuracy |   top_3_scoreline_hit_rate |   top_5_scoreline_hit_rate |   goal_mae |   total_goals_mae |
|:-------------------------|------------:|-----------------------:|---------------------------:|---------------------------:|-----------:|------------------:|
| Dixon-Coles (main model) |        2660 |                 0.1353 |                     0.3455 |                     0.5098 |     0.8981 |            1.4015 |

## Selected model

**Dixon-Coles (main model)** has the lowest backtest log loss (0.9926) and is used as the primary model for 2026-27 predictions. Promoted-team Elo offset used: -87.9 points, derived from 33 real historical promotion events.

## Limitations

- Dixon-Coles is refit approximately every matchweek (10-match chronological chunks), not every single match, for compute-time reasons; within a chunk, later matches technically use a snapshot fit before the chunk's first match rather than immediately before their own kickoff.
- Head-to-head tie-breaking is not implemented in the season simulation (see simulation config).
- No market-odds baseline is included in this comparison (no historical odds source with sufficient coverage was integrated in Phase 1).
- The Dixon-Coles promoted-team offset is now leakage-safe (computed per validation season from only earlier real promotion events, and applied to that season's actual promoted clubs during backtest prediction). The **Elo** promoted-team offset is still a single global constant computed from the full historical dataset -- a smaller, documented remaining gap.
