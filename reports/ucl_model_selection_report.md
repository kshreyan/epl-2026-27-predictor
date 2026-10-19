# UEFA Champions League Model Selection Report

**Genuinely thin backtest -- read with real caution.** UEFA Champions League has only two real cycles (2024-25, 2025-26) to validate on under the current 36-team Swiss-model league phase -- versus 2,000+ real matches for each domestic league in this project. This backtest scores 270 real LEAGUE-PHASE matches (every league-phase round after the very first, which has no real prior data to fit on); real knockout-round results from both historical cycles feed every model's fit but are not themselves scored (knockout-stage prediction is a separate, not-yet-built capability). Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused unchanged from the domestic config (config/model_config.yaml); there is not enough real data here to independently tune them without overfitting to noise.

## Model comparison (lower log loss / Brier / RPS is better)

| model                    |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:-------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only baseline        |         270 |   0.968364 |      0.576658 |                   0.222498 |
| Dixon-Coles (main model) |         270 |   1.06891  |      0.587385 |                   0.224853 |
| Simple Poisson baseline  |         270 |   1.23652  |      0.654754 |                   0.246988 |

## Selected model

**Elo-only baseline** has the lowest backtest log loss (0.9684) and is used as the primary model for 2026-27 league-phase predictions.

## Limitations

- Sample size (see above) is far too small for isotonic calibration (this project's own 500-match minimum) -- raw model probabilities are used uncalibrated.
- No historical market-odds source exists for this competition (no football-data.co.uk coverage) -- no model+market blend backtest could be run; real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Time-decay half-life (269 days) and all other hyperparameters are the domestic, club-football-tuned defaults, not independently validated for this competition's much sparser real match calendar.
- No pre-season strength seed (unlike Nations League's real UEFA-tier Elo seed): both real historical cycles are temporally continuous and mostly share the same clubs year to year, so Elo accumulates real signal from a flat start across both seasons rather than needing one.
