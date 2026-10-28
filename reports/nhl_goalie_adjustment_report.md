# NHL Goalie Adjustment Signal Report

Generated: 2026-10-28T20:08:44+00:00

Real held-out-season test: each team's real prior-season (2024) primary goalie's real shrunk GSAx (MoneyPuck) tested against real season 2025's outcomes, on top of Elo-only (this league's own real moneyline backtest winner). n=1312 real games.

**Real, disclosed scope limitation**: season-level goalie rating, not a live per-game confirmed-starter feature -- see nhl_goalie_rating.py's module docstring for why.

- Elo-only mean log loss: 0.69649
- Elo + goalie-adjusted log loss: 0.68504
- goalie_diff coefficient: -0.31719
- Bootstrap 95% CI: [-0.71825, +0.09606]

## Verdict

**No significant edge found.** The goalie adjustment is not wired into live predictions; Elo-only remains primary. A real, honest result -- a season-level, not live per-game confirmed-starter signal is a real, coarser proxy, and a richer live feature is a real candidate for a later phase, not assumed to arrive automatically.
