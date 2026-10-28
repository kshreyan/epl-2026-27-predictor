# NBA Model+Market Blend Report

Generated: 2026-10-28T20:26:38+00:00

Real backtest on 973 real games with a real closing moneyline (ESPN game-summary pickcenter): Elo-only's own real probability vs. a 50/50 logit-space blend with the real closing line, de-vigged by this league's own real backtested-best method (**power**).

- Model-only mean log loss: 0.61351
- Blend mean log loss: 0.58214
- Bootstrap 95% CI on the edge: [+0.02266, +0.04008]
- Real mean CLV (close - open, home side): +0.0002 over 973 real games

## Verdict

The blend's edge is statistically significant -- blending real market odds in for fixtures with real current market data.
