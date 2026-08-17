# EPL Hyperparameter Tuning Report (Phase 2)

Generated: 2026-08-17T23:34:09+00:00

Held out real season: **2025-26** (380 matches). Trained on all real matches strictly before it (4180 matches). Each trial fits once and evaluates log loss over the full holdout season -- see the module docstring for why this differs from the full walk-forward backtest.

## Dixon-Coles

- Trials: 40
- Baseline (previous config) holdout log loss: 1.0512
- Best found: half_life_days=269.2, l2_reg=0.1234 -> holdout log loss 1.0386

## Elo

- Trials: 40
- Baseline (previous config) holdout log loss: 1.0387
- Best found: k_factor=30.6, home_advantage_elo_points=63.0 -> holdout log loss 1.0375

## Next step

`config/model_config.yaml` has been updated with these values. Re-run `src/evaluation/backtest.py`, `src/calibration/calibrate_probabilities.py`, `src/simulation/simulate_full_season.py`, and `src/models/predict_all_matches.py` to regenerate all downstream outputs with the tuned hyperparameters.
