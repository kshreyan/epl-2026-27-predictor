# UFC Model Selection Report

Real rolling-origin backtest on 3237 real historical fights (2021-01-16 to 2026-10-24, refit every 30 real fights using only data strictly before that point -- no future leakage). UFC has no continuous score margin, so two SEPARATE real models are backtested: a win-probability model (src/models/fighter_elo_model.py, a plain win/loss Elo -- not soccer's/NFL's margin-of-victory-weighted Elo, which has no real analogue for an individual fight), and a Distance Survival model (src/models/fight_distance_model.py) predicting whether a fight ends in a real stoppage -- this project's real equivalent of +2 Margin Survival for this sport.

## Win model comparison (lower log loss / Brier is better)

| model                   |   n_fights |   log_loss |   brier_score |
|:------------------------|-----------:|-----------:|--------------:|
| Fighter Elo (win model) |       3237 |   0.684029 |      0.490925 |
| Flat 50/50 baseline     |       3237 |   0.693147 |      0.5      |

## Distance-survival blend-weight comparison

| model                                               |   n_fights |   log_loss |   brier_score |
|:----------------------------------------------------|-----------:|-----------:|--------------:|
| Distance-survival blend (equal_blend, weight=0.5)   |       3237 |   0.733254 |      0.493174 |
| Distance-survival blend (fighter_only, weight=1.0)  |       3237 |   1.08427  |      0.511393 |
| Distance-survival blend (opponent_only, weight=0.0) |       3237 |   1.34715  |      0.517198 |

Selected blend: **equal_blend** (lowest real backtest log loss) -- used by compute_margin_survival_ufc.py for every real upcoming fight.

## Real historical finish-rate distribution

Overall real share of fights ending in a stoppage (not a decision): **52.9%** across 3297 real historical fights.

Real per-fighter `p_fail` distribution (every real historical fight, both fighters' perspective), the basis for Distance Survival's real risk-tier bands:

| Percentile | p_fail |
|---|---|
| 20th | 0.1981 |
| 40th | 0.2613 |
| 60th | 0.3012 |
| 80th | 0.3745 |

Used directly by compute_margin_survival_ufc.py to set Distance Survival's real risk-tier bands -- see that module's docstring for the exact choice.

## Limitations

- No real market-odds blending (UFC's h2h-only real market, see collect_odds.py, is shown for comparison only, same as every other league's model-only predictions where blending isn't yet wired in).
- One real global Elo rating per fighter, not per weight class -- a fighter who changes weight class keeps their one real rating (see fighter_elo_model.py's module docstring).
- `stoppage_given_loss_probability`'s blend weight is chosen from three real candidates (fighter-only, opponent-only, equal blend) -- a continuously-fit logistic blend is a real, separate possible refinement, not attempted here.
