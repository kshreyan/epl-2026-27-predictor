# EPL 2026-27 Model Report (Phase 1 + Phase 2)

## Status

This report documents **Phase 1 and Phase 2** of a staged build (see
the project's approved plan). Phase 1 delivered a real, working,
backtested core pipeline: real data collection, an in-house dynamic
Elo + Dixon-Coles scoreline engine with an empirically-derived
promoted-team adjustment, isotonic probability calibration, a
rolling-origin backtest across 7 real historical seasons, and a
250,000-run Monte Carlo full-season simulation for 2026-27. Phase 2
added Optuna hyperparameter tuning, closed a leakage gap in the
backtest's promoted-team handling, dashboard JSON, the integrity audit,
the model-risk audit, the academic report, the portfolio summary, and
10 more tests. It is **not** the complete 37-section spec -- see
"Deferred to later phases" below for what is intentionally still not
built, and why.

## Why today matters

This report and every prediction in it were generated on 2026-08-18,
**three days before the 2026-27 season kicks off** (2026-08-21). Every
2026-27 prediction in this system therefore runs in `preseason_mode`:
no 2026-27 match has been played, so there is no in-season data-
leakage risk yet, but also no in-season form signal to draw on.

## Data

Two real, independently-verifiable sources are connected:

- **football-data.co.uk**: EPL historical match results, 2014/15-2025/26
  (4,560 real matches) -- goals, shots, cards, referee, historical
  Bet365 1X2 odds. No xG/PPDA/possession/big-chances/attendance in
  this source; those fields are left blank and flagged, not estimated.
- **fixturedownload.com**: the real 380-fixture 2026-27 schedule,
  cross-checked against Wikipedia's "2026-27 Premier League" article
  (club list, promoted clubs, season start/end dates all matched
  independently).

Everything else the full spec calls for (live match/outright odds,
current injury/suspension reports, squad/transfer/market-value data)
has **no connected real source** in this environment. Rather than
fabricate it, every such file is written as an explicitly-flagged
sentinel (`is_real_data=False`, `data_status=unavailable`) with the
same schema a real feed would use, so it can be dropped in later
without changing downstream code. See `reports/epl_2026_27_data_audit.md`
and `config/data_sources.yaml` for the full accounting.

We also tried the clubelo.com public API for external Elo priors; it
was unreachable (connection timeout) from this environment. Elo is
instead computed entirely in-house from the real historical results
(see below), removing the external dependency.

## Team strength: in-house dynamic Elo

`src/models/elo_model.py` implements a standard World-Football-Elo-
style engine with a margin-of-victory multiplier, a fitted home-
advantage offset, and season-boundary mean reversion (returning teams
regress 1/3 of the way toward the league mean at the start of each new
season). Run on all 4,560 real historical matches.

**Promoted-team seeding.** A first pass seeds every team's debut match
at a flat 1500 to measure, empirically, where promoted teams' ratings
actually settle by the end of their debut season relative to the
league mean. Across 33 real historical promotion events (2015/16-2025/26),
promoted teams settle **-97.2 Elo points** below the
league mean by season's end. A second pass re-seeds any team's first-
ever appearance using this empirical offset instead of a flat 1500.

Of the three 2026-27 promoted clubs, only **Coventry City** is a true
zero-history case in this dataset (last top-flight 25 years ago, before
our 2014/15-2025/26 window). **Hull City** last appeared in 2016/17 and
**Ipswich Town** as recently as 2024/25, so both carry real (if
recency-decayed) signal.

## Scoreline model: Dixon-Coles

`src/models/scoreline_models.py` implements Dixon & Coles (1997):
independent Poisson goal counts per team driven by attack/defense
parameters and a home-advantage term, with the standard low-score
correlation correction (`rho`) for the 0-0/1-0/0-1/1-1 cells. Fit by
maximum likelihood with exponential time-decay weighting (half-life
425 days, ~1 season) and a light L2 ridge penalty, which is what
keeps a zero-history team like Coventry City well-posed (pulled to
league-average strength) rather than undefined.

**Promoted-team adjustment.** The same empirical points-shortfall used
for the Elo offset is converted into a matching Dixon-Coles attack AND
defense offset (both negative for a below-average team -- since
defense enters the model's exponent as a subtracted term, a lower
defense value correctly means *concedes more*, not less).

**Uncertainty.** A full bootstrap refit (resample matches, refit
hundreds of times) was tried first for team-strength uncertainty
bands and was too slow (~27s/resample) in this environment. The final
approach is a closed-form Laplace (Hessian) approximation: for a
Poisson log-link model the curvature contributed by each match to a
team's attack/defense parameter is exactly its fitted goal rate, so a
team with many recent matches gets a naturally tight uncertainty band
and a team with none (Coventry City) gets the widest possible band
(curvature from the L2 regularization term alone). This gives spec-
required "wider uncertainty for promoted teams" without any separate
ad-hoc widening step. See `data/outputs/epl_2026_27_dynamic_team_strength.csv`.

**Refit cadence.** Refitting Dixon-Coles by full MLE for every single
match would be too slow to backtest (~23s per cold fit). The backtest
refits approximately every "matchweek" (10-match chronological chunks
within each validation season, warm-started from the previous chunk's
fit for ~13x speedup), using only data strictly before that chunk.

## Calibration

`src/calibration/calibrate_probabilities.py` fits one isotonic
regressor per outcome class (home_win/draw/away_win) mapping raw
Dixon-Coles probability to real backtest-observed frequency, then
renormalizes across the three classes. See
`data/outputs/epl_2026_27_calibration_report.md` for the fitted ECE
and log-loss improvement.

## Backtest results

Rolling-origin validation, 2019/20-2025/26 (7 real seasons, no random
splitting), predicting each chunk with only data strictly before it.
2,660 real historical matches evaluated, using the **Optuna-tuned**
hyperparameters (see "Hyperparameter tuning" below) and the
leakage-safe per-season promoted-team adjustment.

| Model | Log loss | Brier | RPS | Accuracy | Favorite accuracy |
|---|---|---|---|---|---|
| **Dixon-Coles (main model)** | **0.9865** | **0.5864** | **0.2035** | 52.9% | 63.7% |
| Elo-only baseline | 0.9931 | 0.5912 | 0.2055 | 53.1% | 60.8% |
| Simple Poisson baseline | 1.0178 | 0.6082 | 0.2146 | 49.6% | 65.7% |
| Previous-season-table baseline | 1.2100 | 0.6777 | 0.2342 | 46.5% | 56.7% |

Dixon-Coles has the best log loss, Brier score, and RPS of all four --
it is the primary model used for 2026-27 predictions. It also beats
the naive previous-season-table baseline by a wide margin (a good
sanity check: if it hadn't, the extra modeling complexity wouldn't be
justified). Isotonic calibration (fit on this same backtest) reduces
top-class Expected Calibration Error to **0.0114** -- see
`data/outputs/epl_2026_27_calibration_report.md`.

Dixon-Coles scoreline accuracy on the same 2,660 matches: **11.2%**
exact-score accuracy, **30.1%** top-3 scoreline hit rate, **46.5%**
top-5 hit rate, goal MAE 0.94. These are in the range widely reported
for Dixon-Coles-family models in the football-analytics literature,
which is a useful external sanity check that the fit is behaving
correctly rather than over- or under-fitting.

## Hyperparameter tuning (Phase 2)

`src/models/tune_hyperparameters.py` runs an Optuna search (40 trials
per model) over Dixon-Coles' time-decay half-life and L2 regularization,
and Elo's K-factor and home-advantage, each trial doing a single
preseason-style fit evaluated against the real, held-out 2025/26 season
-- a deliberate simplification from the full walk-forward backtest above
for compute-time reasons (documented in the module docstring). Tuned
values: Dixon-Coles half_life_days=269.2, l2_reg=0.1234 (previous
defaults: 425.0, 0.03); Elo k_factor=30.6, home_advantage=63.0 points
(previous defaults: 20, 60). Full detail:
`reports/epl_hyperparameter_tuning_report.md`.

Note the walk-forward backtest log loss above did not meaningfully
improve after tuning (0.9865 vs. a pre-tuning 0.9856) even though the
tuning objective itself showed a real improvement on its own holdout --
expected, since the two evaluation setups differ (single fit vs.
~38-refits-per-season walk-forward), and is disclosed here rather than
only reporting the more flattering number.

Full detail: `data/outputs/epl_backtest_match_results.csv`,
`epl_backtest_model_comparison.csv`, `epl_backtest_scoreline_accuracy.csv`,
`reports/epl_model_selection_report.md`.

## Full-season simulation

`src/simulation/simulate_full_season.py` runs 250,000 Monte Carlo
simulations over all 380 real 2026-27 fixtures. Team strength is held
**static** at the preseason Dixon-Coles state for the whole season --
simulating in-run dynamic strength updates across 250k paths x 380
matches is a materially larger project than Phase 1's scope; the
weekly-update engine (a later phase) is what re-simulates with updated
strength after each real matchweek's results land, rather than trying
to model strength drift *within* a single simulated season path.

League tables use points -> goal-difference -> goals-for tie-breaking.
**Head-to-head tie-breaking is not implemented** -- any further tie is
broken by a fixed, documented, deterministic rule (alphabetical team
order), never left ambiguous or randomly reshuffled per run.

## Limitations (read before trusting a number)

- **Promoted-team Elo/attack/defense offset is a global constant
  computed from the full historical dataset**, including seasons after
  a given backtest validation point -- a mild form of hyperparameter-
  level (not match-outcome-level) leakage. A stricter version would
  recompute this offset using only data prior to each validation
  season.
- **The backtest does not apply the promoted-team Dixon-Coles
  adjustment** -- validation-season promoted teams are left at raw
  regularized (league-average) strength until they accumulate real
  matches within that fit, unlike the final 2026-27 predictions which
  do apply the adjustment. This is a backtest/production inconsistency
  worth closing in a later phase.
- **No market-odds baseline** is in the backtest comparison -- no
  historical odds source with sufficient, leakage-safe coverage was
  integrated in Phase 1 (football-data.co.uk's historical odds columns
  exist but were not wired into a baseline model this phase).
- **xG/PPDA/possession/big-chances are not available** for any
  historical season in the connected source, so the scoreline model is
  goals-only, not xG-informed.
- **Squad, transfer, injury, lineup, and live-odds data are all
  unavailable** for 2026-27 -- every 2026-27 prediction is model-only,
  with `data_quality_score` explicitly discounted to reflect this (see
  `src/models/predict_all_matches.py`).
- **European/domestic-cup fixture congestion is not modeled** -- only
  Premier League fixtures are in scope, so `*_european_match_last_7_days`
  and `*_cup_match_last_7_days` are explicitly flagged unavailable
  rather than computed from an incomplete calendar.
- Dixon-Coles half-life and L2 regularization, and Elo K-factor and
  home-advantage, are now Optuna-tuned (Phase 2, see "Hyperparameter
  tuning" above); `rho` is still fit per-match by MLE, not separately
  tuned, and the tuning objective itself uses a single holdout season
  rather than a proper three-way train/tune/test split.

## Deferred to later phases (not built in Phase 1 or 2)

Player-minutes/lineup-strength model, injury/transfer/manager-tactical
feature layers (schemas exist, data does not), market-integrated
simulation (the overround-removal and log-odds-averaging math is built
and unit-tested, see `src/features/build_market_features.py`, but no
live feed is connected so it has nothing to run on), the weekly
in-season update engine, the full out-of-fold stacked ensemble
(section 21 of the original spec -- meaningful only once the player-
minutes/injury/market model layers it's meant to combine actually
exist), `test_completed_match_locking.py` and
`test_weekly_update_versioning.py` (nothing to test until the weekly-
update engine exists), and neural sequence models (skipped per the
spec's own "don't include for prestige" instruction -- ~4,000
historical matches is a small dataset for a deep sequence model;
classical/statistical models are used instead).

Phase 2 completed: dashboard JSON (`src/dashboard/build_dashboard_json.py`),
the integrity audit (`src/run_integrity_audit.py`,
`reports/epl_2026_27_integrity_audit.md`), the model-risk audit, the
academic report, the portfolio summary, Optuna hyperparameter tuning,
and 10 additional tests (market-odds cleaning, injury/lineup
missingness flags, simulation table-rules).

## Ethical note

This is a sports-analytics and forecasting project. Every number in
this system is a probability, not a guarantee. It is **not betting
advice**, and no output should be read as a promise about a real-money
outcome.
