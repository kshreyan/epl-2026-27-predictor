# NFL Model+Market Blend Report

Generated: 2026-10-28T19:30:50+00:00

Real backtest on 1314 real historical games: the point-margin model's own real out-of-sample probability vs. a 50/50 logit-space blend with the real closing moneyline, de-vigged by this league's own real backtested-best method (**power** -- see reports/nfl_devig_method_report.md).

- Model-only mean log loss: 0.68394
- Blend mean log loss: 0.62591
- Bootstrap 95% CI on the edge (positive favors the blend): [+0.04798, +0.06830]
- Season majority: 5/5

## Verdict

The blend's edge is statistically significant (CI excludes zero and it wins a season majority) -- blending real market odds in for fixtures with real current market data.
