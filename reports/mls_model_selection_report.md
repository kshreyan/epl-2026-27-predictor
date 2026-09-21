# MLS Model Selection Report (Phase 1)

Rolling-origin backtest, real seasons 2023-2025 (three full real closed seasons -- unlike UEFA Nations League's thin one-cycle history, this is close to a domestic league's own backtest sample size), refit approximately every real MLS round (15-match chronological chunks), predicting only with data strictly before each chunk. 1481 real historical matches evaluated.

## Model comparison (lower log loss / Brier / RPS is better)

| model                          |   n_matches |   log_loss |   brier_score |   ranked_probability_score |
|:-------------------------------|------------:|-----------:|--------------:|---------------------------:|
| Elo-only baseline              |        1481 |     1.057  |        0.6357 |                     0.2192 |
| Dixon-Coles (main model)       |        1481 |     1.0848 |        0.6487 |                     0.2251 |
| Simple Poisson baseline        |        1481 |     1.1111 |        0.6649 |                     0.234  |
| Previous-season-table baseline |        1481 |     1.2374 |        0.7044 |                     0.2414 |

## Selected model

**Elo-only baseline** is used as the primary model for 2026 predictions. Elo-only has a statistically significant edge over Dixon-Coles (paired bootstrap CI [-0.0465, -0.0102], 1/3 seasons) -- BTTS/spread/totals predictions still use Dixon-Coles' scoreline distribution (Elo alone gives no scoreline), the same real limitation as UEFA Nations League; treat those markets as less validated than moneyline for MLS specifically.

## Limitations

- No football-data.co.uk coverage exists for MLS -- no historical market-odds source, so no model+market blend backtest could be run; real current market odds (The Odds API) are shown alongside predictions for comparison only, not blended in.
- Treated as a single combined 30-team table across both conferences, matching this project's existing single-table dashboard shape -- real MLS standings, qualification, and the playoff bracket are separately conference-based and are not reproduced here (see config/leagues.yaml).
- Dixon-Coles/Elo/previous-season-table hyperparameters are reused unchanged from the domestic config (config/model_config.yaml); not independently re-tuned for MLS.
- Expansion-club (e.g. San Diego FC) rating offset uses the same promoted-team-adjustment machinery domestic leagues use for a newly-promoted club -- a real, analogous "no prior top-flight history" situation, not a perfect substitute for real MLS expansion-draft/allocation data.
