# BUNDESLIGA 2026-27 Stacked Ensemble Report (Phase 3, revised)

Generated: 2026-09-16T20:11:51+00:00

Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated on the same 2142 real backtest matches used elsewhere in this project. The meta-learner never sees a fold's own matches when fitting that fold.

## Ensemble vs. Dixon-Coles alone (out-of-fold)

| Metric | Dixon-Coles alone | Stacked ensemble |
|---|---|---|
| Log loss | 1.0026 | 0.9957 |
| Brier score | 0.5976 | 0.5942 |
| RPS | 0.2056 | 0.2045 |

## Statistical significance (paired bootstrap, 10,000 resamples)

- Point estimate (DC log loss − ensemble log loss): +0.0069 (positive = ensemble better)
- 95% CI: [+0.0006, +0.0134] (excludes zero)
- Per-season: ensemble wins 7/7 seasons

| season   |   n_matches |   dc_log_loss |   ensemble_log_loss | ensemble_wins_season   |
|:---------|------------:|--------------:|--------------------:|:-----------------------|
| 2019-20  |         306 |        1.0005 |              0.9958 | True                   |
| 2020-21  |         306 |        1.0156 |              1.0075 | True                   |
| 2021-22  |         306 |        1.0107 |              1.0058 | True                   |
| 2022-23  |         306 |        1.0062 |              1.0002 | True                   |
| 2023-24  |         306 |        0.9761 |              0.9727 | True                   |
| 2024-25  |         306 |        1.0313 |              1.0187 | True                   |
| 2025-26  |         306 |        0.9781 |              0.9695 | True                   |

**The ensemble's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) and it is used for the final 2026-27 predictions.**

## Meta-learner coefficients

|          |   dc_home_win |   dc_draw |   dc_away_win |   elo_home_win |   elo_draw |   elo_away_win |   prevseason_home_win |   prevseason_draw |   prevseason_away_win |   simplepoisson_home_win |   simplepoisson_draw |   simplepoisson_away_win |
|:---------|--------------:|----------:|--------------:|---------------:|-----------:|---------------:|----------------------:|------------------:|----------------------:|-------------------------:|---------------------:|-------------------------:|
| away_win |        -0.531 |     0.124 |         0.438 |         -0.956 |      0.01  |          0.977 |                 0.369 |             0.06  |                -0.399 |                   -0.305 |               -0.071 |                    0.407 |
| draw     |         0.111 |    -0.149 |         0.001 |          0.353 |      0.077 |         -0.466 |                -0.717 |             0.023 |                 0.658 |                   -0.449 |                0.556 |                   -0.143 |
| home_win |         0.42  |     0.025 |        -0.439 |          0.603 |     -0.087 |         -0.511 |                 0.348 |            -0.084 |                -0.26  |                    0.754 |               -0.485 |                   -0.264 |

## Limitations

- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected data sources -- see `reports/epl_2026_27_model_report.md`).
- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.
- The significance decision rule (CI excludes zero AND season majority) is a reasonable but not uniquely-correct threshold; a single-season swing could still flip the majority vote.
