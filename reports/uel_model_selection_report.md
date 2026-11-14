# UEFA Europa League Model Selection Report

**Genuinely thin backtest -- read with real caution.** UEFA Europa League has only 7 real cycles (2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26) to validate on under the current 36-team Swiss-model league phase -- versus 2,000+ real matches for each domestic league in this project. This backtest scores 840 real LEAGUE-PHASE matches (every league-phase round after the very first, which has no real prior data to fit on); real knockout-round results from the real historical cycle(s) feed every model's fit but are not themselves scored (knockout-stage prediction is a separate, not-yet-built capability). Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused unchanged from the domestic config (config/model_config.yaml); there is not enough real data here to independently tune them without overfitting to noise.

## Model comparison (lower log loss / Brier / RPS is better)

| model                         |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only, flat start          |         840 |    1.01093 |      0.604636 |                   0.217952 |
| Elo-only, domestic-Elo-seeded |         840 |    1.01204 |      0.605472 |                   0.218428 |
| Dixon-Coles (main model)      |         840 |    1.06331 |      0.61705  |                   0.222786 |
| Simple Poisson baseline       |         840 |    1.14262 |      0.644939 |                   0.233865 |

## Selected model

**Elo-only, flat start** has the lowest backtest log loss (1.0109) and is used as the primary model for 2026-27 league-phase predictions.

## Cross-competition Elo seed (src/models/cross_competition_elo.py)

44 of this backtest's 140 real historical-window teams have a real domestic Elo rating (EPL/La Liga/Serie A/Bundesliga/Ligue 1) to seed from; the rest start flat at 1500, same as before this existed. Scored as its own candidate ("Elo-only, domestic-Elo-seeded") above, not assumed better: the real backtest result is what decides whether this competition's predictions actually use it -- it did NOT win here, so predictions use the flat-start Elo instead.

## Limitations

- Sample size (see above) is far too small for isotonic calibration (this project's own 500-match minimum) -- raw model probabilities are used uncalibrated.
- No football-data.co.uk coverage exists for this competition, but a real model+market blend backtest does exist via ESPN's real pickcenter odds (collect_espn_continental_cup_odds.py, backtest_continental_cup_market_blend.py) -- see reports/uel_market_blend_report.md for whether that blend is actually significant for this competition; it is only applied in live predictions when it is.
- Time-decay half-life (269 days) and all other hyperparameters are the domestic, club-football-tuned defaults, not independently validated for this competition's much sparser real match calendar.
- The domestic-Elo seed only covers a club playing in one of the 5 domestic leagues this project tracks -- the majority of smaller-league entrants (and every non-European-covered country) get no real cross-competition signal at all.
