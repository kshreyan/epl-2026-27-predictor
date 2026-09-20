# UEFA Nations League Model Selection Report (Phase 1)

**Genuinely thin backtest -- read with real caution.** Nations League has only one prior real cycle (2024-25) to validate on, versus 2,000+ real matches for each domestic league in this project. This backtest scores 141 real matches (every round after the season's first, which has no real prior Nations League data to fit on) -- roughly 5% of a domestic league's sample. Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused unchanged from the domestic config (config/model_config.yaml); there is not enough real Nations League data to independently tune them without overfitting to noise.

## Model comparison (lower log loss / Brier / RPS is better)

| model                    |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:-------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only baseline        |         141 |    1.03838 |      0.622625 |                   0.216115 |
| Simple Poisson baseline  |         141 |    1.49611 |      0.761929 |                   0.256561 |
| Dixon-Coles (main model) |         141 |    2.96579 |      0.840264 |                   0.250634 |

## Selected model

**Elo-only baseline** has the lowest backtest log loss (1.0384) and is used as the primary model for 2026-27 international-break predictions.

## Limitations

- Sample size (see above) is far too small for isotonic calibration (this project's own 500-match minimum) -- raw model probabilities are used uncalibrated.
- No historical market-odds source exists for this competition (no football-data.co.uk coverage) -- no model+market blend backtest could be run; real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- No promoted-team adjustment: every 2026-27 participant already has real matches in the 2024-25 historical data (confirmed directly), so none is needed.
- Time-decay half-life (269 days) and all other hyperparameters are the domestic, club-football-tuned defaults, not independently validated for international football's much sparser real match calendar.
- Elo is seeded from each team's real pre-season League A/B/C/D tier (not flat 1500 for everyone -- see TIER_RATING_OFFSET), a real signal a flat seed was found to get badly wrong with this little data (a real League A side, Switzerland, rated below San Marino). The 300-point top-to-bottom tier gap is a simplifying assumption, not independently validated against real data.
