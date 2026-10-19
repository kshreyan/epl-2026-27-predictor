# UEFA Champions League Model Selection Report

**Genuinely thin backtest -- read with real caution.** UEFA Champions League has only two real cycles (2024-25, 2025-26) to validate on under the current 36-team Swiss-model league phase -- versus 2,000+ real matches for each domestic league in this project. This backtest scores 270 real LEAGUE-PHASE matches (every league-phase round after the very first, which has no real prior data to fit on); real knockout-round results from both historical cycles feed every model's fit but are not themselves scored (knockout-stage prediction is a separate, not-yet-built capability). Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused unchanged from the domestic config (config/model_config.yaml); there is not enough real data here to independently tune them without overfitting to noise.

## Model comparison (lower log loss / Brier / RPS is better)

| model                         |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only, domestic-Elo-seeded |         270 |   0.945983 |      0.560175 |                   0.214506 |
| Elo-only, flat start          |         270 |   0.968364 |      0.576658 |                   0.222498 |
| Dixon-Coles (main model)      |         270 |   1.06891  |      0.587385 |                   0.224853 |
| Simple Poisson baseline       |         270 |   1.23652  |      0.654754 |                   0.246988 |

## Selected model

**Elo-only, domestic-Elo-seeded** has the lowest backtest log loss (0.9460) and is used as the primary model for 2026-27 league-phase predictions.

## Cross-competition Elo seed (src/models/cross_competition_elo.py)

30 of this backtest's 54 real historical-window teams have a real domestic Elo rating (EPL/La Liga/Serie A/Bundesliga/Ligue 1) to seed from; the rest start flat at 1500, same as before this existed. Scored as its own candidate ("Elo-only, domestic-Elo-seeded") above, not assumed better: the real backtest result is what decides whether this competition's predictions actually use it -- it won here.

## Limitations

- Sample size (see above) is far too small for isotonic calibration (this project's own 500-match minimum) -- raw model probabilities are used uncalibrated.
- No historical market-odds source exists for this competition (no football-data.co.uk coverage) -- no model+market blend backtest could be run; real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Time-decay half-life (269 days) and all other hyperparameters are the domestic, club-football-tuned defaults, not independently validated for this competition's much sparser real match calendar.
- The domestic-Elo seed only covers a club playing in one of the 5 domestic leagues this project tracks -- the majority of smaller-league entrants (and every non-European-covered country) get no real cross-competition signal at all.
