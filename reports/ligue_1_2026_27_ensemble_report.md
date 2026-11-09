# LIGUE_1 2026-27 Stacked Ensemble Report (Phase 3, revised)

Generated: 2026-11-09T09:47:58+00:00

Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated on the same 2337 real backtest matches used elsewhere in this project. The meta-learner never sees a fold's own matches when fitting that fold.

## Ensemble vs. Dixon-Coles alone (out-of-fold)

| Metric | Dixon-Coles alone | Stacked ensemble |
|---|---|---|
| Log loss | 1.0108 | 1.0057 |
| Brier score | 0.6040 | 0.6010 |
| RPS | 0.2095 | 0.2078 |

## Statistical significance (paired bootstrap, 10,000 resamples)

- Point estimate (DC log loss − ensemble log loss): +0.0051 (positive = ensemble better)
- 95% CI: [-0.0005, +0.0108] (**straddles zero**)
- Per-season: ensemble wins 6/7 seasons

| season   |   n_matches |   dc_log_loss |   ensemble_log_loss | ensemble_wins_season   |
|:---------|------------:|--------------:|--------------------:|:-----------------------|
| 2019-20  |         279 |        1.0064 |              1.0016 | True                   |
| 2020-21  |         380 |        1.0301 |              1.0257 | True                   |
| 2021-22  |         380 |        1.0136 |              1.0149 | False                  |
| 2022-23  |         380 |        0.992  |              0.992  | True                   |
| 2023-24  |         306 |        1.0364 |              1.0314 | True                   |
| 2024-25  |         306 |        0.9849 |              0.9706 | True                   |
| 2025-26  |         306 |        1.0111 |              0.9997 | True                   |

**The ensemble's apparent edge is NOT statistically significant on this evidence (bootstrap CI straddles zero and/or it does not win a season majority) -- Dixon-Coles alone remains the primary model.** A prior version of this report declared the ensemble primary from a raw 0.0031 log-loss point-estimate gap with no significance test; that was wrong, and this decision now requires both criteria above, computed fresh every time this module runs.

## Meta-learner coefficients

|          |   dc_home_win |   dc_draw |   dc_away_win |   elo_home_win |   elo_draw |   elo_away_win |   prevseason_home_win |   prevseason_draw |   prevseason_away_win |   simplepoisson_home_win |   simplepoisson_draw |   simplepoisson_away_win |
|:---------|--------------:|----------:|--------------:|---------------:|-----------:|---------------:|----------------------:|------------------:|----------------------:|-------------------------:|---------------------:|-------------------------:|
| away_win |        -0.7   |     0.287 |         0.396 |         -0.441 |     -0.261 |          0.685 |                -0.266 |            -0.184 |                 0.433 |                   -0.043 |               -0.558 |                    0.584 |
| draw     |         0.052 |     0.615 |        -0.662 |         -0.425 |      0.217 |          0.212 |                 0.064 |             0.212 |                -0.272 |                   -0.295 |                0.15  |                    0.15  |
| home_win |         0.648 |    -0.902 |         0.266 |          0.867 |      0.043 |         -0.897 |                 0.202 |            -0.029 |                -0.161 |                    0.338 |                0.408 |                   -0.734 |

## Limitations

- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected data sources -- see `reports/epl_2026_27_model_report.md`).
- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.
- The significance decision rule (CI excludes zero AND season majority) is a reasonable but not uniquely-correct threshold; a single-season swing could still flip the majority vote.
