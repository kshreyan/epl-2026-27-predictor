# NFL De-Vig Method Selection Report

Generated: 2026-10-28T19:29:21+00:00

Real backtest on 1359 real historical closing moneylines (American, converted to decimal) against real game outcomes -- each method's own fair probability for the team that actually won, scored by log loss, no model blended in.

| method | log_loss | n_matches |
|---|---|---|
| power | 0.61076 | 1359 |
| shin | 0.61078 | 1359 |
| multiplicative | 0.61102 | 1359 |

**Selected: power** -- used by `select_devig_method('nfl')`.
