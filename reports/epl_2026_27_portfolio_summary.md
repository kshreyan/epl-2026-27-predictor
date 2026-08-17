# Portfolio Summary: EPL 2026-27 Prediction System

A probabilistic forecasting system for the 2026-27 English Premier
League season -- built as a serious sports-analytics, data-science,
predictive-modeling, and simulation project, not a toy or a betting
tool.

## What this demonstrates

**End-to-end data engineering with real, verified sources.** Rather
than working from a pre-cleaned dataset, this project collects its own
data: 4,560 real historical Premier League matches (2014/15-2025/26)
and the real, complete 380-fixture 2026-27 schedule, both from
independently-checkable public sources, cross-validated against a
third source (Wikipedia) for consistency. Every data category with no
connected real source (live odds, injuries, transfers, squad data) is
handled by an explicit, schema-correct "unavailable" sentinel rather
than invented numbers -- a deliberate data-integrity discipline
documented in `reports/epl_2026_27_data_audit.md`.

**Statistical modeling grounded in the sports-analytics literature.**
A dynamic Elo rating system and a Dixon-Coles (1997) bivariate Poisson
scoreline model, both implemented from first principles (not a
black-box library call), including a from-scratch closed-form
uncertainty-quantification method (a Laplace/Hessian approximation)
built after a more obvious approach (bootstrap resampling) was
benchmarked and found too slow -- and the tradeoff was documented
rather than silently swapped in.

**Real backtesting against honest baselines.** Strict time-based
rolling-origin validation across 7 real Premier League seasons (2,660
matches, no random splitting, no data leakage), comparing the primary
model against three simpler baselines it has to actually beat to
justify its complexity. It does: lower log loss, Brier score, and
Ranked Probability Score than an Elo-only model, a previous-season-
table heuristic, and a plain (non-Dixon-Coles) Poisson model. See
`reports/epl_model_selection_report.md`.

**Automated hyperparameter tuning.** An Optuna search over the model's
key hyperparameters (time-decay half-life, regularization strength,
Elo K-factor and home-advantage), evaluated against a real held-out
season, with the tuning methodology's own limitations documented
alongside the result (`reports/epl_hyperparameter_tuning_report.md`).

**Full-season Monte Carlo simulation at scale.** 250,000 simulated
seasons over all 380 real fixtures, vectorized for speed (~37 seconds
for the full run), producing a complete probability distribution over
every club finishing in every one of the 20 league positions --
not just a single predicted table.

**Two real engineering bugs caught and fixed during development, both
documented rather than swept under the rug:** a sign error in the
promoted-team adjustment that made newly-promoted clubs look
defensively *stronger* than they should, and a silent
date-string-formatting mismatch between two pandas code paths that
caused an entire backtest run to silently produce zero results. Both
are described, with root cause, in `reports/epl_2026_27_model_report.md`.

**Calibrated, uncertainty-first outputs.** Every probability is
isotonic-calibrated against real backtest data (measured Expected
Calibration Error: 0.0084). Every team-strength estimate carries an
explicit uncertainty interval that is deliberately wide for
under-observed clubs (a promoted team with zero historical top-flight
data gets the widest band in the league, automatically, not by manual
override). The system's own risk audit
(`reports/epl_2026_27_model_risk_audit.md`) states plainly where it is
least reliable, rather than presenting uniform confidence.

**A staged, honestly-scoped build.** Rather than claiming a
100+-file spec was fully built in one pass, this project was delivered
in phases with an explicit, written accounting of what's real, what's
tuned, what's backtested, and what's deliberately deferred (player-
minutes modeling, live market integration, weekly in-season updates,
a dashboard) -- because no real data source for those pieces exists in
this environment yet, and fabricating one would defeat the entire
premise of the project.

## Explicitly not betting advice

Every output is a probability -- "projected probability," "expected
points," "confidence," "upset risk" -- never a guarantee. This project
exists to demonstrate forecasting methodology, not to generate
wagering recommendations, and should not be used as such.

## Where to look

- `reports/epl_2026_27_model_report.md` -- full methodology and limitations
- `reports/epl_2026_27_data_audit.md` -- what's real vs. flagged, with sources
- `reports/epl_model_selection_report.md`, `reports/epl_hyperparameter_tuning_report.md` -- backtest and tuning results
- `reports/epl_2026_27_model_risk_audit.md` -- where the model is least reliable
- `reports/epl_2026_27_integrity_audit.md` -- automated consistency checks
- `data/outputs/epl_2026_27_expected_table.csv`, `epl_2026_27_position_distribution.csv` -- the season forecast itself
