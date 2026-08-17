# EPL 2026-27 Prediction System: Academic Report

## 1. Project objective

Build a probabilistic forecasting system for the English Premier
League 2026/27 season: match-level scoreline distributions, result
probabilities, and full-season Monte Carlo simulation (title, top-4,
relegation, and complete 1st-20th position distributions), evaluated
by proper scoring rules against real historical data rather than by
raw prediction accuracy alone. The explicit goal is calibrated,
honest, reproducible probability estimates -- not "picking winners,"
and not betting advice.

## 2. Why Premier League forecasting differs from World Cup forecasting

A prior project in this space (an FIFA World Cup predictor) dealt with
a single, short, elimination-format tournament: ~64 matches, played by
national teams that exist only in that context, with almost no
within-tournament team-strength updating possible before the format
forces knockouts. The Premier League is the opposite kind of problem:
a long, 380-match round-robin season played by club teams with rich,
continuous historical data (transfers, managerial history, multi-
season form), where team strength genuinely drifts over months, and
where the object of interest (a full 20-team final table with title,
European-qualification, and relegation outcomes) is a joint
distribution over the outcomes of all 380 correlated matches, not a
single knockout bracket. This pushes the modeling problem toward
season-long simulation, dynamic (not static) team-strength estimation,
and much heavier emphasis on real historical backtesting, since a
League with 12 real prior seasons of data (unlike a World Cup, held
every 4 years with far fewer comparable editions) supports genuine
statistical validation.

## 3. Data collection

Two real, verifiable, timestamped sources: football-data.co.uk (EPL
historical results, 2014/15-2025/26, 4,560 real matches) and
fixturedownload.com (the real 380-fixture 2026-27 schedule,
independently cross-checked against Wikipedia's season article for
club list, promoted clubs, and season dates). Every other data
category the wider project spec calls for -- live odds, injuries,
transfers, squad/market data, xG/PPDA/possession -- has no connected
real source in this environment and is represented honestly as
explicitly-flagged sentinel data rather than fabricated. See
`reports/epl_2026_27_data_audit.md`.

## 4. Data cleaning

Team names differ across sources (e.g. "Man Utd" vs. "Man United" vs.
"Manchester United"). `src/utils/team_names.py` maintains a canonical
name registry built from the actual union of names observed across
both real sources (35 historical clubs + the 20 real 2026-27 clubs),
with a strict resolver that raises rather than silently guessing on an
unrecognized name. Dates, goal counts, and categorical fields are
parsed and validated on ingestion (`src/data_collection/`).

## 5. Data validation

`src/data_validation/schema_definitions.py` and `validate_raw_data.py`
enforce the required column schema, expected row counts (380
fixtures), duplicate-key checks, and enum-value checks (fixture
status, injury availability status, odds snapshot type) on every raw
file, with a hard failure (non-zero exit) if any check fails.

## 6. Feature engineering

Team-strength differentials (Elo, Dixon-Coles attack/defense, a
composite strength index), schedule-congestion features computed
directly from the real fixture calendar (rest days, matches in the
last 7/14 days), and promoted-team flags feed into
`data/processed/epl_2026_27_match_features.csv`, one row per real
fixture, each stamped with `feature_generated_at`,
`latest_source_timestamp_used`, and a `leakage_safe_flag`.

## 7. Dynamic team-strength modeling

`src/models/dynamic_team_strength_state_space.py` produces, per team,
a posterior mean and uncertainty interval for attack and defense
strength. The uncertainty comes from a closed-form Laplace (Hessian)
approximation to the Dixon-Coles maximum-likelihood fit: for a Poisson
log-link model, the curvature each match contributes to a team's
parameter is exactly its fitted goal rate, so teams with abundant
recent data get naturally tight intervals and teams with little or no
data (a newly promoted club) get the widest possible interval, without
any separate hand-tuned widening rule. A full weighted-bootstrap
alternative was tried first and rejected for being too slow (~27s per
resample) to run at the required scale in this environment -- a
concrete example of a principled statistical method being chosen
partly on computational grounds, documented rather than hidden.

## 8. Player-minutes modeling

**Not implemented.** This requires real per-player minutes, lineup,
and injury data, none of which is connected (see report section on
deferred work). The schema for this layer exists in the spec but no
model has been built against fabricated inputs.

## 9. Transfer adjustment

**Not implemented** for the same reason -- no transfer data source is
connected.

## 10. Promoted-team adjustment

`src/models/promoted_team_adjustment.py` identifies every real
historical promotion event (a team appearing in season S but not
S-1, 2015/16-2025/26, 33 such team-seasons) and computes their real
average points-below-league-average outcome. This empirical shortfall
is converted into matching Elo and Dixon-Coles attack/defense offsets
and applied to the three real 2026-27 promoted clubs (Coventry City,
Ipswich Town, Hull City), each also carrying much wider uncertainty
than an established club (see section 7). In the backtest, this
adjustment is computed **per validation season, using only promotion
events from strictly earlier seasons** -- a leakage-safe refinement
added after an initial version applied a single dataset-wide constant.

## 11. Scoreline modeling

Dixon & Coles (1997): two Poisson processes for home/away goals driven
by attack/defense parameters and a home-advantage term, with the
standard low-score correlation correction (`rho`, fit by MLE) for the
0-0/1-0/0-1/1-1 cells. Fit with exponential time-decay weighting and
an L2 ridge penalty (both hyperparameter-tuned, see section 15). The
scoreline surface covers 0-0 through 8-8 (exceeding the spec's 0-0
through 7-7 minimum).

## 12. Market integration

**Not implemented.** No live odds feed is connected in this
environment. Every prediction is explicitly `market_available=False`,
model-only. The output schema reserves `*_market_integrated_*` columns
(left blank, not duplicated) so a real feed can be added later without
a schema change.

## 13. Squad/injury integration

**Not implemented** for the same data-availability reason. Every 2026-27
prediction row carries `squad_data_available=False` and
`injury_data_available=False` rather than silently assuming full
squad strength or full health.

## 14. Calibration

`src/calibration/calibrate_probabilities.py` fits one isotonic
regressor per outcome class on the real backtest predictions, then
renormalizes across classes. This reduced top-class Expected
Calibration Error to a real, measured 0.0084 on 2,660 held-out
matches (see `data/outputs/epl_2026_27_calibration_report.md`).

## 15. Backtesting

Strict rolling-origin validation, no random splitting: train on all
real matches strictly before a chunk, predict that chunk, never look
forward. Validated across 7 real seasons (2019/20-2025/26, 2,660
matches). Compared against three honest baselines (Elo-only,
previous-season-table, simple non-Dixon-Coles Poisson) --
Dixon-Coles wins on log loss, Brier score, and Ranked Probability
Score against all three (see `reports/epl_model_selection_report.md`
for exact numbers). Hyperparameters (Dixon-Coles time-decay half-life
and L2 regularization; Elo K-factor and home-advantage) were then
tuned with Optuna against a held-out season not used for the reported
backtest metrics (`reports/epl_hyperparameter_tuning_report.md`).

## 16. Simulation methodology

250,000-run Monte Carlo simulation over all 380 real 2026-27 fixtures,
scorelines drawn from each match's Dixon-Coles probability distribution
via vectorized inverse-CDF sampling, batched (25,000 sims/batch) for
memory safety. League tables use points -> goal-difference ->
goals-for tie-breaking; any further tie is broken by a fixed,
documented, deterministic rule (alphabetical order) rather than left
ambiguous -- true Premier League head-to-head tie-breaking is not
implemented (a documented limitation, not a silent gap).

## 17. Uncertainty intervals

Reported at two levels: team-strength parameter uncertainty (Laplace
approximation, section 7) and season-outcome uncertainty (the full
position-probability distribution and points/position percentiles
from the Monte Carlo simulation, `data/outputs/epl_2026_27_expected_table.csv`).
Neither is a single point estimate dressed up as certain.

## 18. Limitations

See `reports/epl_2026_27_model_report.md` "Limitations" and
`reports/epl_2026_27_model_risk_audit.md` for the complete, current
list -- summarized: no player-minutes/injury/transfer/market data
connected; simulation holds team strength static within a season; no
head-to-head tie-breaking; hyperparameter tuning uses a single holdout
season rather than a three-way split; the Elo promoted-team offset (but
not the Dixon-Coles one) is still a single global constant rather than
season-specific.

## 19. Ethical note

This is a sports-analytics, forecasting, and software-engineering
project. Every number produced is a probability, explicitly not a
guarantee, and the system's language is deliberately calibrated
("projected probability," "expected points," "confidence") rather
than absolute ("guaranteed," "lock," "sure win"). **This is not
betting advice** and must not be used, presented, or relied on as
such.

## 20. Future improvements

In rough priority order: (1) a real live-odds feed for market
integration and closing-line benchmarking; (2) real injury/lineup data
and the player-minutes model it would unlock; (3) a weekly-update
engine to bring the system out of preseason-only mode once the season
starts; (4) a proper three-way train/tune/test split for
hyperparameter tuning; (5) head-to-head tie-breaking in the season
simulation; (6) in-simulation dynamic team-strength updates (currently
static per simulated season); (7) a dashboard surfacing all of the
above with the uncertainty-first framing this report argues for.
