# NCAAB Model+Market Blend Report

Generated: 2026-11-14T12:35:46+00:00

Real backtest on 4519 real historical games (one real recent season -- see collect_espn_college_basketball_odds.py for the real closing-line collection's own deliberate scope limit): this league's own real primary moneyline model (elo_home_win) vs. a 50/50 logit-space blend with the real closing moneyline, de-vigged by this league's own real backtested-best method (**multiplicative**).

- Model-only mean log loss: 0.59358
- Blend mean log loss: 0.56206
- Bootstrap 95% CI on the edge (positive favors the blend): [+0.02768, +0.03542]
- Season majority: 1/1

## Verdict

The blend's edge is statistically significant (CI excludes zero and it wins a season majority) -- blending real market odds in for fixtures with real current market data.
