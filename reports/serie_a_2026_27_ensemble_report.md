# SERIE_A 2026-27 Stacked Ensemble Report (Phase 3, revised)

Generated: 2026-09-16T19:05:25+00:00

Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated on the same 2660 real backtest matches used elsewhere in this project. The meta-learner never sees a fold's own matches when fitting that fold.

## Ensemble vs. Dixon-Coles alone (out-of-fold)

| Metric | Dixon-Coles alone | Stacked ensemble |
|---|---|---|
| Log loss | 0.9926 | 0.9799 |
| Brier score | 0.5908 | 0.5835 |
| RPS | 0.1991 | 0.1960 |

## Statistical significance (paired bootstrap, 10,000 resamples)

- Point estimate (DC log loss − ensemble log loss): +0.0127 (positive = ensemble better)
- 95% CI: [+0.0057, +0.0199] (excludes zero)
- Per-season: ensemble wins 7/7 seasons

| season   |   n_matches |   dc_log_loss |   ensemble_log_loss | ensemble_wins_season   |
|:---------|------------:|--------------:|--------------------:|:-----------------------|
| 2019-20  |         380 |        1.0004 |              0.984  | True                   |
| 2020-21  |         380 |        0.9586 |              0.9531 | True                   |
| 2021-22  |         380 |        1.0058 |              0.989  | True                   |
| 2022-23  |         380 |        1.0027 |              0.9924 | True                   |
| 2023-24  |         380 |        0.9994 |              0.9826 | True                   |
| 2024-25  |         380 |        0.986  |              0.9651 | True                   |
| 2025-26  |         380 |        0.9956 |              0.9932 | True                   |

**The ensemble's edge is statistically significant (bootstrap CI excludes zero AND it wins a season majority) and it is used for the final 2026-27 predictions.**

## Meta-learner coefficients

|          |   dc_home_win |   dc_draw |   dc_away_win |   elo_home_win |   elo_draw |   elo_away_win |   prevseason_home_win |   prevseason_draw |   prevseason_away_win |   simplepoisson_home_win |   simplepoisson_draw |   simplepoisson_away_win |
|:---------|--------------:|----------:|--------------:|---------------:|-----------:|---------------:|----------------------:|------------------:|----------------------:|-------------------------:|---------------------:|-------------------------:|
| away_win |        -0.02  |    -0.681 |         0.656 |         -0.831 |     -0.012 |          0.797 |                -0.227 |            -0.26  |                 0.442 |                   -0.566 |               -0.184 |                    0.704 |
| draw     |        -0.386 |     0.822 |        -0.359 |         -0.147 |      0.134 |          0.089 |                 0.092 |             0.386 |                -0.402 |                   -0.067 |                0.536 |                   -0.393 |
| home_win |         0.407 |    -0.14  |        -0.297 |          0.978 |     -0.122 |         -0.886 |                 0.135 |            -0.126 |                -0.04  |                    0.633 |               -0.353 |                   -0.311 |

## Limitations

- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected data sources -- see `reports/epl_2026_27_model_report.md`).
- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.
- The significance decision rule (CI excludes zero AND season majority) is a reasonable but not uniquely-correct threshold; a single-season swing could still flip the majority vote.
