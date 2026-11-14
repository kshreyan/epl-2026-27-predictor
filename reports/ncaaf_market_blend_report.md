# NCAAF Model+Market Blend Report

Generated: 2026-11-14T12:03:12+00:00

Real backtest on 22 real historical games (one real recent season -- see collect_espn_ncaaf_odds.py for the real closing-line collection's own deliberate scope limit): this league's own real primary moneyline model (elo_home_win) vs. a 50/50 logit-space blend with the real closing moneyline, de-vigged by this league's own real backtested-best method (**multiplicative**).

- Model-only mean log loss: 0.54571
- Blend mean log loss: 0.52850
- Bootstrap 95% CI on the edge (positive favors the blend): [-0.04108, +0.07300]
- Season majority: 1/1

## Verdict

**No significant edge found** -- the CI does not exclude zero, or the blend does not win a real season majority. Model-only predictions remain primary; market odds are still shown for comparison only, not blended in. This is a real, honest result, not a bug.
