# NFL LightGBM Model Report

Generated: 2026-10-28T19:43:01+00:00

Real held-out-season test: trained on real seasons [2021, 2022, 2023, 2024] (inner Optuna tuning on a walk-forward split inside that window only), tested on real season 2025, never touched during tuning.

Best hyperparameters: `{'num_leaves': 8, 'learning_rate': 0.010019163947823312, 'min_child_samples': 36, 'n_estimators': 47}`

## Real log loss on the held-out season

- LightGBM: 0.68997
- Point-margin model (same season, from backtest_team_sport.py): 0.67830

Bootstrap 95% CI on the edge (positive favors LightGBM): [-0.02832, +0.00517]

## Verdict

**No significant edge found.** LightGBM is not wired into live predictions; the point-margin model remains primary. This is a real, honest result on real data -- a single held-out season (272 games) is a small real sample for detecting a GBM's edge over an already-strong baseline, and more real seasons of data (or richer real features, e.g. play-by-play EPA) are the most likely path to a different real result later, not assumed to arrive automatically.
