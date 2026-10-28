# NBA Rest-Day Adjustment Signal Report

Generated: 2026-10-28T20:18:13+00:00

Real held-out-season test: real rest-day differential (capped at 5, derived purely from real game dates) tested against real season 2025-26's outcomes, on top of Elo-only (this league's own real moneyline backtest winner). n=1233 real games.

- Elo-only mean log loss: 0.61276
- Elo + rest-adjusted log loss: 0.60032
- rest_diff coefficient: 0.02947
- Bootstrap 95% CI: [-0.09574, +0.15877]

## Verdict

**No significant edge found.** The rest adjustment is not wired into live predictions; Elo-only remains primary. A real, honest result, not a bug.
