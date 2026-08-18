# EPL 2026-27 Stacked Ensemble Report (Phase 3, revised)

Generated: 2026-08-18T03:00:32+00:00

Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated on the same 2660 real backtest matches used elsewhere in this project. The meta-learner never sees a fold's own matches when fitting that fold.

## Ensemble vs. Dixon-Coles alone (out-of-fold)

| Metric | Dixon-Coles alone | Stacked ensemble |
|---|---|---|
| Log loss | 0.9865 | 0.9834 |
| Brier score | 0.5864 | 0.5853 |
| RPS | 0.2035 | 0.2031 |

## Statistical significance (paired bootstrap, 10,000 resamples)

- Point estimate (DC log loss − ensemble log loss): +0.0032 (positive = ensemble better)
- 95% CI: [-0.0021, +0.0087] (**straddles zero**)
- Per-season: ensemble wins 3/7 seasons

| season   |   n_matches |   dc_log_loss |   ensemble_log_loss | ensemble_wins_season   |
|:---------|------------:|--------------:|--------------------:|:-----------------------|
| 2019-20  |         380 |        0.9716 |              0.9762 | False                  |
| 2020-21  |         380 |        1.0275 |              1.018  | True                   |
| 2021-22  |         380 |        0.9538 |              0.9549 | False                  |
| 2022-23  |         380 |        1.0192 |              0.9938 | True                   |
| 2023-24  |         380 |        0.9198 |              0.9226 | False                  |
| 2024-25  |         380 |        0.9706 |              0.9803 | False                  |
| 2025-26  |         380 |        1.0433 |              1.0379 | True                   |

**The ensemble's apparent edge is NOT statistically significant on this evidence (bootstrap CI straddles zero and/or it does not win a season majority) -- Dixon-Coles alone remains the primary model.** A prior version of this report declared the ensemble primary from a raw 0.0031 log-loss point-estimate gap with no significance test; that was wrong, and this decision now requires both criteria above, computed fresh every time this module runs.

## Meta-learner coefficients

|          |   dc_home_win |   dc_draw |   dc_away_win |   elo_home_win |   elo_draw |   elo_away_win |   prevseason_home_win |   prevseason_draw |   prevseason_away_win |   simplepoisson_home_win |   simplepoisson_draw |   simplepoisson_away_win |
|:---------|--------------:|----------:|--------------:|---------------:|-----------:|---------------:|----------------------:|------------------:|----------------------:|-------------------------:|---------------------:|-------------------------:|
| away_win |        -1.185 |     0.401 |         0.803 |         -0.554 |     -0.2   |          0.774 |                 0.202 |             0.012 |                -0.194 |                    0.382 |               -0.431 |                    0.068 |
| draw     |         0.173 |     0.252 |        -0.436 |         -0.131 |     -0.132 |          0.253 |                -0.067 |             0.111 |                -0.054 |                   -0.761 |                0.917 |                   -0.167 |
| home_win |         1.012 |    -0.653 |        -0.367 |          0.685 |      0.333 |         -1.027 |                -0.135 |            -0.123 |                 0.249 |                    0.379 |               -0.486 |                    0.099 |

## Limitations

- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected data sources -- see `reports/epl_2026_27_model_report.md`).
- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.
- The significance decision rule (CI excludes zero AND season majority) is a reasonable but not uniquely-correct threshold; a single-season swing could still flip the majority vote.
