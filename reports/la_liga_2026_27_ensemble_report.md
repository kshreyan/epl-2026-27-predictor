# LA_LIGA 2026-27 Stacked Ensemble Report (Phase 3, revised)

Generated: 2026-11-09T09:47:29+00:00

Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated on the same 2660 real backtest matches used elsewhere in this project. The meta-learner never sees a fold's own matches when fitting that fold.

## Ensemble vs. Dixon-Coles alone (out-of-fold)

| Metric | Dixon-Coles alone | Stacked ensemble |
|---|---|---|
| Log loss | 0.9941 | 0.9857 |
| Brier score | 0.5921 | 0.5865 |
| RPS | 0.1996 | 0.1969 |

## Statistical significance (paired bootstrap, 10,000 resamples)

- Point estimate (DC log loss − ensemble log loss): +0.0085 (positive = ensemble better)
- 95% CI: [+0.0025, +0.0145] (excludes zero)
- Per-season: ensemble wins 5/7 seasons

| season   |   n_matches |   dc_log_loss |   ensemble_log_loss | ensemble_wins_season   |
|:---------|------------:|--------------:|--------------------:|:-----------------------|
| 2019-20  |         380 |        1.0026 |              1.0044 | False                  |
| 2020-21  |         380 |        1.0178 |              1.0033 | True                   |
| 2021-22  |         380 |        1.009  |              0.9946 | True                   |
| 2022-23  |         380 |        1.0065 |              0.9952 | True                   |
| 2023-24  |         380 |        0.9637 |              0.9524 | True                   |
| 2024-25  |         380 |        0.9722 |              0.974  | False                  |
| 2025-26  |         380 |        0.9872 |              0.9759 | True                   |

**The ensemble's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) and it is used for the final 2026-27 predictions.**

## Meta-learner coefficients

|          |   dc_home_win |   dc_draw |   dc_away_win |   elo_home_win |   elo_draw |   elo_away_win |   prevseason_home_win |   prevseason_draw |   prevseason_away_win |   simplepoisson_home_win |   simplepoisson_draw |   simplepoisson_away_win |
|:---------|--------------:|----------:|--------------:|---------------:|-----------:|---------------:|----------------------:|------------------:|----------------------:|-------------------------:|---------------------:|-------------------------:|
| away_win |        -0.127 |    -0.269 |         0.36  |         -0.891 |      0.568 |          0.287 |                -0.184 |            -0.334 |                 0.481 |                   -0.277 |               -0.709 |                    0.949 |
| draw     |        -0.343 |     0.511 |        -0.152 |          0.028 |      0.087 |         -0.1   |                 0.002 |            -0.035 |                 0.049 |                   -0.53  |                0.918 |                   -0.373 |
| home_win |         0.471 |    -0.242 |        -0.207 |          0.863 |     -0.655 |         -0.187 |                 0.183 |             0.369 |                -0.53  |                    0.807 |               -0.209 |                   -0.576 |

## Limitations

- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected data sources -- see `reports/epl_2026_27_model_report.md`).
- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.
- The significance decision rule (CI excludes zero AND season majority) is a reasonable but not uniquely-correct threshold; a single-season swing could still flip the majority vote.
