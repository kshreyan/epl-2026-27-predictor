# EPL 2026-27 Model Report (Phase 1 + Phase 2 + Phase 3 + Phase 4)

## Status

This report documents **Phases 1-4** of a staged build (see the
project's approved plan). Phase 1 delivered a real, working, backtested
core pipeline: real data collection, an in-house dynamic Elo +
Dixon-Coles scoreline engine with an empirically-derived promoted-team
adjustment, isotonic probability calibration, a rolling-origin backtest
across 7 real historical seasons, and a 250,000-run Monte Carlo
full-season simulation for 2026-27. Phase 2 added Optuna hyperparameter
tuning, closed a leakage gap in the backtest's promoted-team handling,
dashboard JSON, the integrity audit, the model-risk audit, the academic
report, the portfolio summary, and 10 more tests. Phase 3 added a
backtested stacked ensemble of the four models with real data behind
them, and a weekly-update engine. Phase 4 added a paired-bootstrap
significance test that found the ensemble's apparent edge over
Dixon-Coles was not statistically distinguishable from noise (95% CI
straddles zero, wins only 3/7 backtest seasons) -- **Dixon-Coles alone
is the primary model**, not the ensemble -- plus a provenance audit and
a real investigation of the three previously-deferred data feeds (see
"Deferred to later phases"). It is **not** the complete 37-section spec
-- see that section for what is intentionally still not built, and why.
Post-Phase-4 (after the dashboard was live), a statistical-rigor pass
found and fixed a season-level overconfidence bug in the Monte Carlo
simulation -- see "Season-level calibration" below for the full
diagnosis, fix, before/after numbers, and a new season-level
calibration backtest.

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

## Stacked ensemble (Phase 3, revised)

`src/models/final_stacked_model.py` stacks the four base models that
have real data behind them (Dixon-Coles, Elo, previous-season-table,
simple Poisson) with a multinomial logistic-regression meta-learner,
evaluated with proper 5-fold out-of-fold prediction on the same 2,660
real backtest matches. Its raw point-estimate log loss is lower than
Dixon-Coles alone (0.9834 vs. 0.9865, a 0.0031 gap) -- **but a paired
bootstrap (10,000 resamples over matches) puts the 95% CI on that gap
at [-0.0021, +0.0087], straddling zero, and the ensemble wins only 3
of 7 individual backtest seasons.** On ~2,660 matches the standard
error of a log-loss estimate is comparable to the point-estimate gap
itself, so the gap is not distinguishable from noise on this evidence.

**Dixon-Coles alone remains the primary model.** An earlier version of
this report declared the ensemble primary from the point estimate
alone, with no significance test -- that was a real methodological gap
(flagged during external review), now fixed: `fit_final_meta_learner()`
requires both the bootstrap CI to exclude zero AND a season majority
before the ensemble is used, computed fresh on every run against the
current backtest (not hardcoded), so a future genuine improvement can
still turn it on automatically, and any regression turns it back off.
See `reports/epl_2026_27_ensemble_report.md` for the full per-season
breakdown.

## Weekly-update engine (Phase 3)

`src/update_after_matchweek.py` implements spec section 27: given a
real, caller-supplied CSV of a matchweek's completed results
(match_id, home_goals, away_goals, source_name, source_timestamp), it
locks them into `data/raw/epl_2026_27_completed_matches.csv` (same
schema as the historical results file, so it concatenates directly for
refitting), marks those fixtures `completed`, refits Elo/Dixon-Coles
on historical + completed 2026-27 data, re-predicts every remaining
fixture (`prediction_mode=early_week_mode`), and re-runs the season
simulation with the real results-to-date locked in as a fixed baseline
for every simulated path (`src/simulation/simulate_full_season.run_monte_carlo`,
generalized from the preseason-only version to accept this baseline).
A previously-completed match's original pre-match prediction is never
overwritten -- only the real result is appended alongside it, so
prediction-vs-outcome accuracy stays auditable.

**Audited and extended, post-Phase-4**: an audit of this engine found
it refit team strength correctly (a) but had no durable, provably-
leak-free record of what was predicted before each kickoff (b), no
scoring pass at all once results landed (c), and -- appropriately,
since 10 matches/gameweek is too small a sample to recalibrate on --
no automatic recalibration (d), though no *gated* version existed
either. Three new pieces close (b), (c), and a properly-gated version
of (d):

- **`src/evaluation/prediction_ledger.py`**: every prediction this
  pipeline ever generates for a match -- the initial preseason run and
  every subsequent weekly refresh for a still-unplayed fixture -- gets
  its own permanent row, written via a real file *append*
  (`open(path, "a")`), never a read-modify-rewrite cycle, so an
  existing row cannot be mutated even in principle (asserted directly
  in `tests/test_prediction_ledger.py`, not just designed that way).
  `select_pre_kickoff_predictions` picks, per match, the most recent
  ledger row whose `generated_at` is strictly before that match's own
  `kickoff_utc` -- and asserts this on every row it returns, raising
  if a match has no such row rather than silently scoring a leaked or
  missing prediction. Verified against the real 380-fixture preseason
  ledger: all 380 rows pass the leak-check.
- **`src/evaluation/score_weekly_results.py`**: runs automatically
  inside `run_update()` right after a matchweek's results are locked.
  **Horizon-aware, two tracks, never pooled**: every metric is computed
  separately for the **preseason** track (the frozen
  `preseason-2026-27-v2` tag's predictions, read directly from git via
  `prediction_ledger.load_preseason_ledger` -- the ledger itself did
  not exist yet as of that tag, so this cannot come from the live
  ledger) and the **operational** track (the latest pre-kickoff
  prediction at any point in the season). Per-gameweek and cumulative
  log loss/Brier/RPS for the production prediction, the raw
  (uncalibrated) Dixon-Coles baseline captured at prediction time (so
  no baseline is ever reconstructed from a since-refit model), and a
  real market baseline (see below). Also a running (non-horizon)
  reliability table per track, a **horizon-stratified reliability
  table** bucketing every pre-kickoff prediction ever logged for a
  completed match (not just the latest) by days-before-kickoff (0-2,
  3-7, 8-30, 31+) -- answering "how calibrated are predictions made X
  days out", a different question from "how calibrated is our current
  best guess" -- a "most surprising results" list, and an append-only
  season-level title/top-4/relegation probability path.
- **Real match-level 1X2 odds are now connected**: no live odds feed
  exists in this environment (needs a user-supplied `ODDS_API_KEY`,
  see `collect_real_odds.py`), so
  `src/data_collection/collect_match_odds.py` -- the per-fixture
  counterpart to the season-outright odds snapshot above -- accepts a
  manually-entered, de-vigged 1X2 snapshot per match_id, preserved on
  every re-run exactly like the outright-odds collector. All 10 real
  gameweek-1 fixtures now carry a real snapshot (ESPN/DraftKings,
  captured 2026-08-19, 2-3 days before kickoff -- not confirmed to be
  the literal closing line). `prediction_ledger.append_to_ledger` pulls
  these into the ledger's `market_*` fields at append time (a scoring
  baseline, deliberately separate from `PREDICTION_COLUMNS`'
  `*_market_integrated` fields, which remain unused). Verified against
  the real ledger: 10/380 matches now score a genuine market baseline;
  the model and market disagree most on Ipswich Town (13.9% model vs
  34.9% market win probability for their opener against Sunderland) --
  consistent with the same Ipswich-specific gap already flagged in
  "Market comparison" above. **Update, 2026-08-21**: a blended model+
  market prediction feature -- described here as "still-unbuilt" --
  was subsequently built, validated, and wired into live predictions
  via a different, separate mechanism (not these unused
  `*_market_integrated` columns); see "Model+market blend" below.
- **`src/evaluation/recalibration_gate.py`**: explicitly NOT an
  automatic recalibration loop, tightened after a second review found
  the first version's single ~20-match recent holdout and bare point-
  estimate win too loose for a decision that swaps production's
  calibrator. Now: **150 real matches minimum** (`MIN_MATCHES_TO_ATTEMPT`,
  up from 60) before the gate is even eligible; **rolling-origin
  evaluation** across the whole season so far (real matches walked
  forward in ~10-match chunks, a challenger refit before each chunk on
  historical backtest + all real matches strictly before it, evaluated
  on that chunk -- one paired observation per real match across every
  chunk, not just a recent slice); promotion requires a **paired
  bootstrap (10,000 resamples) 95% CI on the log-loss difference that
  excludes zero on the challenger-is-better side** (`ci_low > 0`), the
  same statistical bar already used for the ensemble-vs-Dixon-Coles
  decision, not a bare point estimate; a **fixed evaluation cadence**
  (every 5th matchweek, `EVALUATION_CADENCE_MATCHWEEKS`) rather than a
  Bonferroni correction, to control repeated testing across a 38-week
  season; and the challenger is restricted to **temperature scaling**
  (`softmax(log(p_raw) / T)`, a single scalar parameter) below
  `ISOTONIC_MIN_REAL_MATCHES` (500) real matches -- since a Premier
  League season is only 380 matches, this challenger uses temperature
  scaling for the entire 2026-27 season; isotonic (used unchanged for
  the INCUMBENT, which never touches real data) only becomes eligible
  for the challenger in a future season once enough real matches have
  accumulated across seasons. Every attempt, promoted or not, is
  appended to `epl_2026_27_recalibration_decisions.csv` with its exact
  numbers. `tests/test_recalibration_gate.py` verifies: a real no-op
  below the threshold and off-cadence, every attempt logged regardless
  of outcome, a genuine promotion (full bootstrap CI on the
  challenger's side) when real data carries exploitable signal the
  static backtest didn't have, a logged rejection when it doesn't, and
  the temperature-scaling/isotonic method switch at the 500-match
  threshold.

**This still cannot be exercised against real 2026-27 results**: today
(2026-08-20) is one day before kickoff (2026-08-21). All of the
above is verified against synthetic scores for real matchweek-1
fixtures, written only to a temporary directory via an injectable
`WeeklyUpdatePaths` (now covering the ledger, scoring, and
recalibration paths too) -- never to the real project data files
(`tests/test_completed_match_locking.py`,
`tests/test_weekly_update_versioning.py`,
`tests/test_prediction_ledger.py`, `tests/test_score_weekly_results.py`,
`tests/test_recalibration_gate.py`). The versioning test confirms two
separate weekly-update runs produce two distinct run_ids that are both
appended to the experiment log, never overwriting each other's
timestamp -- spec section 33's explicit requirement.

### Automated trigger: no human pastes in a results CSV

Everything above runs the moment `run_update()` is called with a real
matchweek and a real results file -- but something still had to
*supply* that call. Two new pieces close that gap:

- **`src/data_collection/fetch_live_results.py`**: fetches real,
  currently-completed 2026-27 results from football-data.co.uk's
  live-updating current-season CSV (the same real source
  `collect_historical_results.py` already uses for 2014/15-2025/26;
  its current-season file gets new rows appended within a day or two
  of matches being played). Maps each result to its real `match_id` in
  `epl_2026_27_fixtures.csv` via team name + `normalize_team_name`
  (raising, never guessing, on an unrecognized name -- same discipline
  as every other real collector here) and raises if a completed result
  has no matching fixture (a real data-integrity signal, never
  silently dropped). Verified live against the real endpoint: correctly
  returns 0 results right now (the 2026-27 season file does not exist
  yet on football-data.co.uk pre-kickoff -- confirmed via direct
  request, HTTP 300, not an error condition), and the parsing/matching
  logic itself is tested against synthetic CSV text mirroring the real
  column format (`tests/test_fetch_live_results.py`).
- **`src/weekly_auto_update.py`**: determines which matchweek (if any)
  has newly and *fully* concluded -- every one of its real fixtures has
  a real result available, not just the first one or most of them,
  since gameweeks don't always finish on the same day once
  postponements/rearrangements happen -- and is not already locked.
  Calls `run_update()` for each newly-complete matchweek in
  chronological order (required: each matchweek's own pre-kickoff
  prediction must reflect only the matchweeks strictly before it), then
  rebuilds the dashboard JSON. A genuine no-op (no lock, no refit, no
  commit) on any day nothing has newly concluded --
  `tests/test_weekly_auto_update.py` verifies the no-op case, the
  detection logic, chronological ordering across a multi-week gap, and
  a full end-to-end run (real refit/predict/simulate/score/
  recalibration-gate path, live-results fetch replaced with a fixed
  in-memory result set) that correctly becomes a no-op on a second call
  once that matchweek is already locked.
- **`.github/workflows/weekly_update.yml`**: runs
  `python -m src.weekly_auto_update` daily (06:00 UTC) plus on manual
  dispatch, after a fast-test-suite safety check. Results themselves
  need no key (a public CSV) -- but as of 2026-08-21 the workflow also
  refreshes live match odds every run via `collect_odds.py`, reading
  `ODDS_API_KEY` from a GitHub Actions repository secret (added by the
  user; 1 credit/call, well under the free tier's 500/month at daily
  cadence), so `data/raw/epl_2026_27_real_odds.csv` -- and the
  prediction ledger's `market_*` scoring baseline it feeds -- stays
  current automatically rather than frozen at whatever was last fetched
  by hand. Commits and pushes if anything changed (a locked gameweek,
  or just fresh odds), which in turn triggers `deploy.yml`.

Full detail: `data/outputs/epl_backtest_match_results.csv`,
`epl_backtest_model_comparison.csv`, `epl_backtest_scoreline_accuracy.csv`,
`reports/epl_model_selection_report.md`.

## Full-season simulation

`src/simulation/simulate_full_season.py` runs 250,000 Monte Carlo
simulations over all 380 real 2026-27 fixtures. Team strength is held
fixed **within** a single simulated season path (no in-run strength
drift -- the weekly-update engine is what re-simulates with updated
strength after each real matchweek's results land, rather than
modeling drift *within* one simulated path), but as of this report
**each of the 250,000 simulated seasons now draws its own team
attack/defense sample** from the Dixon-Coles fit's Laplace-approximated
standard errors, rather than every simulation reusing the same fixed
point estimate. See "Season-level calibration" immediately below for
why this changed and what it did to the numbers.

League tables use points -> goal-difference -> goals-for tie-breaking.
**Head-to-head tie-breaking is not implemented** -- any further tie is
broken by a fixed, documented, deterministic rule (alphabetical team
order), never left ambiguous or randomly reshuffled per run.

## Season-level calibration

Match-level calibration (ECE 0.0114, see "Calibration" above) says
nothing about whether *season-level* aggregates -- title, top-4,
relegation probabilities -- are calibrated. A model can price every
match's 1X2 correctly and still be badly overconfident about who wins
the league, because a season compounds 38 correlated match outcomes
through a table. This section was added after a direct challenge to
two numbers in an earlier verification pass: a 50.3% title favourite
and near-100% relegation probabilities for multiple promoted clubs
simultaneously, which is not a plausible preseason forecast.

### 1. Diagnosis: was parameter uncertainty being propagated?

No. Before this fix, `simulate_full_season.py` called what was then
`build_score_distributions(fixtures_df, fit)` **once**, outside the
Monte Carlo batch loop, using only `fit.attack` / `fit.defense` /
`fit.home_advantage` -- the Dixon-Coles point estimates. Every one of
the 250,000 simulated seasons then drew match scorelines from that
same fixed set of per-fixture score distributions. Only match-outcome
randomness (which scoreline happens, given a team's rating) was being
modeled; the rating itself -- which the Laplace/Hessian fit already
carries a standard error for -- never varied across simulations. That
made the *season* Monte Carlo systematically overconfident even though
the underlying Dixon-Coles fit's match-level probabilities were
properly calibrated: 250,000 independent draws from the same
distribution converge to a sharp estimate of "how a team of exactly
this rating performs over 38 games," which is a much narrower question
than "how good is this team, really, and how does *that* team perform
over 38 games."

### 2. Fix: per-simulation parameter draws, and what it changed

`TeamStrengthUncertainty` (`simulate_full_season.py`) now draws a
fresh attack/defense sample per simulated season from
`Normal(fit.attack, fit.attack_se)` / `Normal(fit.defense,
fit.defense_se)`, clipped to the empirical attack/defense range, before
simulating that season's 380 matches from the draw. This is a Laplace
(Hessian) approximation, already computed by the existing Dixon-Coles
fit for other purposes -- propagating it into the season simulation
was the missing step, not new machinery.

A first version of this fix clipped the *drawn* value to the empirical
range but left the raw standard error uncapped. For a genuinely
(near-)zero-history club the Hessian SE is close to degenerate
(Coventry City and Hull City: SE~2.0 in log-attack-space, vs ~0.14 for
an established club, comparable in size to the entire empirical attack
range) -- so most draws fell outside the clip bounds and piled up
exactly at the boundary, i.e. Coventry got drawn as literally the best
team in the league on a large fraction of simulated seasons. Caught
before it shipped: it produced a ~16% *title* probability for a
promoted club. The final version replaces a promoted team's raw SE
with an empirically-derived one instead of capping it: the standard
deviation of `points_below_league_avg` across all 33 real historical
promotion events (2015/16-2025/26 dataset window), mean -17.6, **std
12.5**, converted through the same points-to-log-rate scaling already
used for the mean promoted-team offset (`/100`) to give
**promoted_se ~= 0.125**. Established clubs keep their raw Laplace SE
unchanged (all under 0.35 in this fit).

Real production numbers, same 250,000-simulation preseason run, same
seed, before and after (`data/outputs/epl_2026_27_expected_table.csv`,
before = git history at the commit immediately prior to this fix):

| | Before (fixed point estimate) | After (parameter uncertainty) |
|---|---|---|
| Arsenal title probability | 50.30% | 43.71% |
| Man City title probability | 43.32% | 38.57% |
| Liverpool title probability | 3.98% | 6.88% |
| Coventry City relegation probability | 75.72% | 59.77% |
| Hull City relegation probability | 78.64% | 62.56% |
| Ipswich Town relegation probability | 99.96% | 99.28% |
| Sunderland relegation probability | 6.90% | 12.11% |
| Leeds United relegation probability | 5.95% | 10.51% |
| Crystal Palace relegation probability | 8.28% | 10.85% |
| Tottenham Hotspur relegation probability | 7.71% | 10.33% |

The title race widened (top-2 combined share dropped from 93.6% to
82.3%, with meaningfully more mass reaching Liverpool and the
mid-table chasers). Relegation mass shifted materially off the three
promoted clubs and onto the established/borderline clubs that a real
relegation battle actually involves -- Sunderland, Leeds, Palace, and
Tottenham each roughly doubled. Ipswich Town (real 2024/25 top-flight
data: 22 points, relegated in last place) stays close to 99% either
way -- that number was never resting on the promoted-team offset, it's
driven by Ipswich's own actual, poor recent Dixon-Coles fit.
Relegation probabilities still sum to exactly 3.0 and title
probabilities to exactly 1.0 in both versions (an invariant of how the
Monte Carlo tallies finishing positions, not a calibration claim).

**Superseded, see section 5 below**: the claim in the previous
paragraph that Ipswich's ~99% "was never resting on the promoted-team
offset" turned out to be wrong in the way that mattered -- it wasn't
resting on the offset *alone*, but the offset was still being added on
top of Ipswich's own real data, and that stacking is precisely what
kept it near 99%. Left as originally written above rather than edited
after the fact; the correction is in section 5, not a silent rewrite
of this one.

### 3. Promoted-team adjustment: what prior, what window

`promoted_team_adjustment.py` fits the promoted-team offset on the
**full historical window** used by the pipeline (2015/16-2025/26, 33
promotion events) -- not a short recent window, so "overlearned on the
seasons where all three promoted clubs went down" does not describe
what was happening. What *is* real: promoted-team relegation outcomes
are volatile across that window, not stationary. 2023/24 and 2024/25
each saw all 3 promoted clubs relegated (6/6), against a long-run
33-event average relegation rate of 51.5%. A single point-estimate
offset (mean `points_below_league_avg = -17.6`) cannot represent that
volatility at all -- it was issue #1 (no parameter uncertainty), not
issue #3, that was actually suppressing this. With `promoted_se`
derived from the same 33-event history's **standard deviation** (12.5
points, ~0.125 in log-rate space) rather than just its mean, the
season simulation can now produce both a promoted club having a
Leeds-2020/21-style respectable finish (+6.1 points above league
average, the best any promoted club has managed in this dataset) and a
promoted club having a well-below-average season, in the correct
proportions, instead of being locked to one fixed shortfall value for
all three clubs every simulated season.

### 4. Season-level calibration backtest

For each of the 7 real seasons already used in the match-level
backtest (2019/20-2025/26), `src/evaluation/season_calibration_backtest.py`
refits Dixon-Coles + the promoted-team adjustment using **only match
data strictly before that season's first ball** (no mid-season
refitting -- this checks the *preseason* forecast, matching what the
2026-27 forecast actually is), runs the same 250,000-simulation
parameter-uncertainty Monte Carlo over that season's real fixtures, and
compares the resulting title/top-4/relegation probabilities against
what actually happened. 140 team-season observations (7 seasons x 20
teams).

| Target | N | N positive | Brier score | Log loss | Brier score, uniform no-skill baseline |
|---|---|---|---|---|---|
| Title | 140 | 7 | 0.02507 | 0.08124 | 0.0475 |
| Top-4 | 140 | 28 | 0.09031 | 0.30202 | 0.16 |
| Relegation | 140 | 21 | 0.08968 | 0.28769 | 0.1275 |

The uniform baseline predicts every team the same probability every
season (7/140, 28/140, 21/140 respectively -- "no information, just
the base rate"). The model beats it by roughly half on Brier score for
all three targets, meaning the probabilities carry real discriminative
information, not just a correctly-centered but flat guess. (The
"mean predicted probability equals the empirical base rate" check that
a calibration report would normally lead with is **not** informative
here and is deliberately left out of this table: probabilities sum to
exactly 1 / 4 / 3 per season by construction, so that equality holds by
arithmetic regardless of whether the model has any skill at all.)

Concrete calibration checks:

- The model's highest-title-probability team was the actual champion
  in **4 of 7 seasons (57%)**. The misses: 2019/20 and 2024/25, both
  seasons where Liverpool won the title but the model favoured
  Manchester City (10.7% predicted for Liverpool in 2024/25 -- a real
  underestimate, not a rounding artifact). 2025/26 was a near-miss:
  Arsenal actually won at a predicted 27.4%, essentially tied with
  Manchester City's 29.2% -- the model correctly saw it as a close
  two-horse race, it just picked the other horse.
- Across all 140 team-seasons, only **one** case of a team predicted
  under 5% relegation probability that was actually relegated:
  Leicester City, 2022/23 (0.96% predicted) -- a season widely
  regarded as a genuine shock relegation, not a case the model should
  be expected to have seen coming from preseason data alone.
- **Zero** cases of a team predicted over 80% relegation probability
  that survived -- no catastrophic overconfidence in that direction
  across 140 observations.
- Promoted-team relegation calibration: across the 21 promoted-team-
  season observations in the backtest, mean predicted relegation
  probability was **61.1%** against an actual realized relegation rate
  of **57.1%** -- close, mildly overconfident, not badly so. In the two
  extreme real seasons (2023/24, 2024/25: 3/3 promoted clubs relegated
  both times), the model predicted a *combined* promoted-club
  relegation probability of only ~1.7 out of 3 (~57%) in each case,
  underestimating the actual outcome (3/3) -- because, correctly, it
  was using only data available *before* that season, which had not
  yet seen this volatility. `promoted_se` grew from 0.084 (12
  promotion events known as of the 2019/20 forecast) to 0.122 (30
  events known as of the 2025/26 forecast) as the backtest window
  progressed and that real volatility accumulated into the historical
  record. The actual 2026-27 forecast uses the full 33-event history
  including both 6/6 seasons, so it carries more of that volatility
  than any individual backtest year could have.

**Honest limitations of this backtest**: N=140 is small for a
season-level calibration check (7 independent season-draws, not 140
independent observations -- the 20 teams within a season are
correlated through the same table). A formal reliability diagram
(binned predicted-vs-actual) was not built for this reason; with this
few positive cases per bucket it would be more noise than signal. This
backtest evaluates the *current* (parameter-uncertainty) simulation
only -- the old fixed-point-estimate simulator was not separately
re-run across all 7 historical seasons for a rigorous head-to-head
comparison, since that code path no longer exists in the working tree
(available via git history at the commit before this fix, if that
comparison is wanted later). The single-season theoretical argument
in "Diagnosis" above, plus the real 2026-27 before/after table in
section 2, are the evidence available for the specific claim that the
fix reduced overconfidence; this backtest instead answers the
separate, complementary question of whether the *current* model is
calibrated at all at the season level, using real out-of-sample
history -- and the answer is: reasonably well, with the two honest
misses (Liverpool's two titles, Leicester's shock relegation) named
explicitly rather than smoothed over.

### 5. Second pass: promoted teams were double-counted, not zero-variance

A follow-up review flagged that Ipswich Town barely moved after the
section-2 fix (99.96% -> 99.28%) while Coventry and Hull moved ~15
points, and hypothesized that promoted-club ratings were being drawn
from a deterministic prior with no variance term at all, resampled for
established clubs but held fixed for promoted ones.

**That specific hypothesis does not hold** -- Coventry and Hull do
resample every simulation (section 2's fix applies to all three
promoted clubs identically). The real mechanism is different and
specific to Ipswich: `apply_promoted_team_adjustment`
(`scoreline_models.py:189`) unconditionally adds the same generic
`points_below_league_avg / 100` shortfall to every promoted club's
attack AND defense, regardless of whether that club already has real,
substantially-weighted Premier League data reflecting its actual
quality. Real numbers pulled directly from the production fit
(time-decay half-life 269 days):

| Team | Real PL history in this dataset | Attack before offset (SE) | Defense before offset (SE) | Defense after offset |
|---|---|---|---|---|
| Coventry City | 0 matches | 0.000 (SE 2.01) | 0.000 (SE 2.01) | -0.176 |
| Hull City | 76 matches, most recent May 2017 -- 9 years stale, decayed to near-nothing at this half-life | -0.004 (SE 1.99) | -0.015 (SE 1.99) | -0.191 |
| Ipswich Town | 38 matches, full 2024/25 season, ending May 2025 -- still roughly half-weighted | -0.181 (SE 0.35) | **-0.456** (SE 0.23) | **-0.632** |

Coventry and Hull are genuinely blank-slate -- their historical data
has decayed to irrelevance, so the generic offset is the right tool.
Ipswich is not blank-slate: it already carries a real, substantially-
weighted, badly-below-average defense rating from actually being
relegated last season. Adding the same generic "-17.6 points" shortfall
on top double-counts that signal -- Ipswich's defense parameter ends up
roughly 1.2 full log-rate units below Arsenal's, a gap section 2's
widened-but-still-fixed-mean SE (0.125, which was in fact *narrower*
than Ipswich's own real fitted SE of 0.348) could never plausibly
close.

**Fix**: `compute_promoted_team_rating_distribution`
(`promoted_team_adjustment.py`) fits a single-season Dixon-Coles model
to each of the 33 real historical promotion events individually (2015/16
-2025/26, one fit per season using only that season's ~380 matches, a
very long half-life so no within-season decay distorts it) and reads
off each promoted club's own REALISED debut-season attack/defense. This
gives a real empirical joint distribution -- attack mean -0.222 (std
0.217), defense mean -0.288 (std 0.223), positive attack-defense
correlation ~0.29 -- built entirely from what promoted clubs have
actually turned out to be, never from what any one club's own
(possibly stale, possibly double-counted) fit says. In the season
simulation, all three of 2026-27's promoted clubs now draw their
(attack, defense) JOINTLY from this same distribution, independently
per simulation, replacing the offset-adjusted mean entirely rather than
only widening its SE.

**Stated trade-off**: this also means Ipswich's own specific 2024/25
signal no longer informs the simulation's promoted-team ratings at
all -- only the generic cross-sectional prior does. That discards real,
club-specific information (a below-average finish two years running is
arguably informative about Ipswich specifically, not just "promoted
clubs in general") in exchange for removing the double-count. It also
means all three of 2026-27's promoted clubs are now statistically
interchangeable in the simulation's eyes -- their relegation
probabilities converge to nearly the same value (see below), whereas
before the fix, real match data \[wrongly\] gave the appearance of
differentiating them. Whether a hybrid that shrinks Ipswich's own
real fit toward this prior -- rather than replacing it outright -- would
be more accurate is a legitimate open question, not resolved here.

Real production numbers, same 250,000-simulation preseason run:

| | Section 2 (SE-only fix) | Section 5 (empirical joint prior) |
|---|---|---|
| Ipswich Town relegation probability | 99.28% | **72.14%** |
| Coventry City relegation probability | 59.77% | 72.00% |
| Hull City relegation probability | 62.56% | 71.96% |
| Title/top-4 probabilities (established clubs) | -- | materially unchanged (Arsenal 43.7% -> 43.8% title) |

Full title and relegation tables, every club, same run:

| Team | Title probability |
|---|---|
| Arsenal | 43.81% |
| Manchester City | 38.49% |
| Liverpool | 6.79% |
| Manchester United | 2.17% |
| Aston Villa | 1.38% |
| Chelsea | 1.32% |
| Newcastle United | 1.23% |
| AFC Bournemouth | 0.93% |
| Brighton & Hove Albion | 0.87% |
| Brentford | 0.85% |
| Nottingham Forest | 0.57% |
| Sunderland | 0.41% |
| Leeds United | 0.40% |
| Fulham | 0.26% |
| Everton | 0.20% |
| Tottenham Hotspur | 0.15% |
| Crystal Palace | 0.12% |
| Hull City | 0.015% |
| Coventry City | 0.010% |
| Ipswich Town | 0.008% |
| **Sum** | **1.0000** |

| Team | Relegation probability |
|---|---|
| Ipswich Town | 72.14% |
| Coventry City | 72.00% |
| Hull City | 71.96% |
| Sunderland | 12.57% |
| Crystal Palace | 11.48% |
| Leeds United | 11.20% |
| Tottenham Hotspur | 11.13% |
| Everton | 8.34% |
| Fulham | 7.67% |
| Nottingham Forest | 4.36% |
| Brentford | 3.19% |
| Brighton & Hove Albion | 3.06% |
| AFC Bournemouth | 2.98% |
| Newcastle United | 2.20% |
| Chelsea | 2.19% |
| Aston Villa | 2.02% |
| Manchester United | 1.25% |
| Liverpool | 0.27% |
| Manchester City | 0.007% |
| Arsenal | 0.003% |
| **Sum** | **3.0000** |

No club exceeds ~90% relegation probability (previous ceiling: 99.96%
for Ipswich). The season-level calibration backtest was re-run with
this fix (leakage-safe: each historical season's promoted-team
distribution is refit from only the promotion events strictly before
that season, same discipline as the mean-offset version):

| Target | Brier score (SE-only fix) | Brier score (empirical joint prior) |
|---|---|---|
| Title | 0.02507 | 0.02508 |
| Top-4 | 0.09031 | 0.09029 |
| Relegation | 0.08968 | **0.08874** |

Title and top-4 are essentially unchanged (expected -- this fix only
touches promoted-club ratings). Relegation Brier improved modestly.
Promoted-team relegation calibration across the 21 backtest
observations: mean predicted 61.6% vs actual realized rate 57.1%
(previously 61.1% vs 57.1%) -- a small, real improvement, not a large
one, because most backtest-era promoted clubs did NOT have Ipswich's
specific situation (a *recent* full season of real top-flight data):
Sheffield United's 2023/24 recall is the closest historical analogue,
and even that gap (2020/21 relegation to 2023/24 promotion, ~2.5 years)
had decayed further than Ipswich's 15-month gap. This bug's impact was
therefore real but concentrated almost entirely in the live 2026-27
forecast, not spread evenly across the historical backtest -- which is
exactly why a season-level calibration backtest alone would not have
caught it; it took a human noticing one club's number didn't move.

## Market comparison

Every number above was checked against the model's own backtest, never
against a real external market -- there was no benchmark that would
have flagged a 50.3% preseason title favourite as implausible before a
human did. `data/raw/epl_2026_27_outright_odds.csv` now carries one
real, manually-entered, de-vigged snapshot: title-winner and relegation
odds for the 10 shortest-priced teams in each market, from
sportsbettingdime.com (DraftKings Sportsbook, multi-book-averaged),
dated 2026-08-06 -- 15 days before kickoff. This is a one-time
snapshot, not a live feed (see "Limitations" for the live-odds gap);
`implied_probability_no_vig` is normalized *within the 10-team listed
subset* (title to sum 1.0, relegation to sum 3.0), since the source
page does not print all 20 teams for either market -- an approximation
that treats the unlisted ~10 teams per market as having negligible
probability, which is reasonable here since the truncation cutoff
lines up with materiality (bottom-half teams omitted from title,
top-half teams omitted from relegation) but is not a full 20-team
book. Do not use these rows to influence match-level or season-level
predictions -- they exist for comparison only.

| Team | Model title probability | Market title probability (no-vig) |
|---|---|---|
| Arsenal | 43.8% | 34.3% |
| Manchester City | 38.5% | 23.5% |
| Liverpool | 6.8% | 13.7% |
| Manchester United | 2.2% | 11.1% |
| Chelsea | 1.3% | 9.9% |
| Tottenham Hotspur | 0.1% | 4.2% |
| Aston Villa | 1.4% | 1.8% |
| Newcastle United | 1.2% | 0.6% |
| Brighton & Hove Albion | 0.9% | 0.6% |
| Leeds United | 0.4% | 0.4% |

| Team | Model relegation probability | Market relegation probability (no-vig) |
|---|---|---|
| Hull City | 72.0% | 79.5% |
| Ipswich Town | 72.1% | 59.4% |
| Coventry City | 72.0% | 59.4% |
| Sunderland | 12.6% | 25.4% |
| Fulham | 7.7% | 15.9% |
| Leeds United | 11.2% | 14.7% |
| Crystal Palace | 11.5% | 13.6% |
| Nottingham Forest | 4.4% | 11.9% |
| Brentford | 3.2% | 10.6% |
| Newcastle United | 2.2% | 9.5% |

(Numbers as of the section 5 fix above -- promoted-club ratings drawn
from the empirical joint historical prior. Title-market table is
essentially unchanged from the section-2 version; only the relegation
table moved meaningfully.)

This is a genuinely mixed picture, reported as it came out rather than
selectively:

- **Arsenal and Manchester City's title odds validate the user's prior
  going into this fix, and partially validate the fix itself but not
  completely.** The market prices Arsenal at 34.3% -- comfortably
  under the "high thirties" ceiling a preseason favourite rarely
  exceeds -- while the pre-fix model said 50.3% and the post-fix model
  now says 43.7%. The fix closed most of the gap to the market (50.3%
  -> 43.7%, market at 34.3%) but did not fully close it. The remaining
  ~9-point gap on Arsenal and a similar gap on Manchester City is a
  real, named, unresolved discrepancy, not evidence the model is now
  "fixed" in an absolute sense -- only that it moved substantially in
  the right direction.
- **Liverpool and Manchester United run the other way**: the model
  underrates both relative to the market (Liverpool 6.9% vs 13.7%,
  Man United 2.1% vs 11.1%). The market may be pricing squad/transfer
  information this goals-only model has no access to (see
  "Limitations"); this is a plausible, named explanation, not a
  confirmed one.
- **Ipswich Town's gap against the market has closed substantially,
  but not entirely, after the section-5 fix.** Before that fix: model
  99.3% vs market 59.4%, a 40-point gap driven by a real double-
  counting bug (Ipswich's own bad 2024/25 data plus a redundant generic
  promoted-team offset stacked on top -- see "Season-level
  calibration" section 5). After: model 72.1% vs market 59.4%, a
  12.7-point gap -- the single largest remaining bug this comparison
  found was real, and fixing it moved the number by 27 points in the
  market's direction. The residual 12.7-point gap is plausibly the
  market pricing real preseason information (squad rebuild, transfer
  activity, a new manager) that this goals-only model has no access to
  at all now that Ipswich's own historical signal has been replaced by
  a generic cross-sectional prior -- see section 5's stated trade-off.
- **A side effect worth naming plainly**: fixing Ipswich made Coventry
  City's market alignment slightly *worse*, not better. Before the fix,
  Coventry (59.8%) was within 0.4 points of the market (59.4%) --
  coincidentally close, not because the model had real signal on
  Coventry specifically (it has zero real PL history in this dataset).
  After the fix, all three promoted clubs are pooled to the same
  empirical prior and converge to ~72%, widening Coventry's gap to the
  market to 12.6 points. This is the direct, honest consequence of
  treating all three clubs identically per section 5's explicit
  methodology, not a new bug -- but it means "the model agrees with the
  market" was never a safe read on Coventry specifically; it was
  coincidence.

## Model+market blend

A direct question -- "will model+market be better than model alone?"
-- got a direct, evidence-based answer instead of a guess, using the
same statistical bar the stacked ensemble was held to
(`src/models/market_blend_model.py`).

**The blend**: a 50/50 average, in log-odds space, of the model's own
probability and the market's de-vigged probability
(`build_market_features.log_odds_average`, already used and tested for
cross-bookmaker averaging -- reused unchanged, just fed a
(model, market) pair instead of a (bookmaker, bookmaker) pair). No
blend weight is fit or tuned -- an untuned 50/50 log-opinion-pool is
the standard default absent other information, and fitting a weight on
this sample would risk exactly the overfitting this project has
already been careful to avoid elsewhere (see the recalibration gate's
temperature-scaling-not-isotonic choice, same reasoning). Only **one**
candidate was tested, once -- not several weights compared post-hoc,
which would itself be a form of the leakage this project has spent
real effort catching in other places.

**Real historical market odds, not synthetic**: football-data.co.uk's
own closing "Avg" columns (the average closing price across every
bookmaker they track) -- already cached locally from the original
historical-results collection (`data/external/football_data_co_uk/`,
tracked in git), no new network call needed. Full coverage confirmed
directly: 2,660/2,660 matches across all 7 backtest seasons
(2019/20-2025/26), 0 missing.

**Result**: the blend beat Dixon-Coles alone far more decisively than
the ensemble ever did.

| | Dixon-Coles alone | Model+market blend | Stacked ensemble (for reference) |
|---|---|---|---|
| Log loss | 0.9865 | **0.9717** | 0.9834 |
| Brier | 0.5864 | **0.5772** | 0.5853 |
| RPS | 0.2035 | **0.1993** | 0.2031 |

Paired bootstrap (10,000 resamples): log-loss difference (DC minus
blend) point estimate **+0.0148**, 95% CI **[+0.0106, +0.0192]** --
entirely positive, nowhere near zero. The blend beat Dixon-Coles in
**7 of 7** backtest seasons, not just a majority. Both promotion
conditions the ensemble was held to (CI excludes zero AND wins a
season majority) are cleared comfortably; the effect size here (0.0148)
is roughly 5x the ensemble's own (non-significant) point estimate of
0.0031. This makes intuitive sense in a way the ensemble result never
quite did: a real betting market aggregates information (injuries,
lineups, team news, public and professional money) a goals-only model
structurally cannot see, so a genuine edge here is exactly what
sports-forecasting theory would predict -- unlike stacking four
variants of the same goals-only signal together, which is what the
ensemble was actually doing.

**Wired into live predictions, 2026-08-21**: `build_model_context`
calls `evaluate_market_blend()` fresh on every run (cheap -- no
refitting, ~1 second) and only applies the blend, per fixture, where
BOTH the blend is significant AND real market odds actually exist for
that specific fixture (`predict_fixtures` checks the latter via
`prediction_ledger.load_combined_match_odds` -- the same live-API-
preferred-over-manual-snapshot source already feeding the ledger's
scoring baseline). A new `market_blend_applied` column on every
prediction row records which ones got it. Verified against the real
pipeline: 10 of 380 current predictions have it applied (matchweek 1,
the only fixtures with a real market posted right now) -- e.g. Ipswich
Town's win probability against Sunderland moved from 13.9% (model-
only) to 23.2% (blended), pulled toward the market's 35.2%, the same
Ipswich gap already flagged in "Market comparison" above. Tested with
both synthetic data (`tests/test_market_blend_model.py`: a challenger
with genuine signal gets promoted, one without does not, coverage
gaps are never estimated) and a real fitted context
(`tests/test_market_blend_wiring.py`: blend applies only to fixtures
with real odds, never to fixtures without, even when globally
significant).

**Honest scope note**: the backtest compared the blend against
Dixon-Coles's own *raw* (pre-calibration) probability -- the same
`dc_home_win`/`dc_draw`/`dc_away_win` columns the ensemble was tested
against, for direct comparability -- not against the fully calibrated/
ensemble/promoted-challenger production pipeline the blend is actually
layered on top of in live predictions. Isotonic calibration mainly
affects per-class calibration (ECE) rather than raw log loss, and an
effect this large and this consistent (7/7 seasons) is very unlikely
to reverse after calibration, but this was not separately re-verified
against the exact calibrated pipeline -- a real, named gap in the
validation, not a hidden one.

## BTTS, spread, and totals predictions

Beyond the 1X2 moneyline, the model now predicts three more betting
markets for every one of the 380 fixtures, every gameweek: both-teams-
to-score (BTTS), Asian Handicap (spread), and Over/Under 2.5 goals
(totals). All three are derived from the same Dixon-Coles scoreline
matrix already computed for the moneyline prediction -- no separate
model (`src/models/scoreline_models.py`: `btts_probability`,
`total_goals_probabilities`, `asian_handicap_home_cover_probability`,
`model_fair_handicap_line`).

**Real market data, where it genuinely exists**: The Odds API confirmed
to support `spreads` and `totals` for this sport (`collect_odds.py` now
requests `h2h,spreads,totals` together); confirmed to explicitly NOT
support `btts` (`INVALID_MARKET` error, tested directly, not assumed).
football-data.co.uk's cached historical files have real closing-line
Asian Handicap (`AHh`/`AvgAHH`/`AvgAHA`) and Over/Under 2.5
(`Avg>2.5`/`Avg<2.5`) columns for backtesting; they have no BTTS column
anywhere. **BTTS therefore has no real market source, live or
historical, and stays honestly model-only** -- not a gap that was
skipped, a gap that was checked and confirmed absent.

**Spread and totals blends, validated the same way the moneyline blend
was** (`src/models/spread_totals_blend_model.py`): a 50/50 log-odds
blend of the model's own probability and the real market's de-vigged
probability, tested via the same paired-bootstrap bar (10,000
resamples, 95% CI must exclude zero AND win a season majority) against
the full 7-season real historical backtest. Both cleared it decisively:

| Market | Model-only log loss | Blend log loss | Bootstrap CI (model &minus; blend) | Season wins |
|---|---|---|---|---|
| Spread (Asian Handicap) | 0.7108 | **0.6969** | [+0.0101, +0.0176] | 7/7 |
| Totals (Over/Under 2.5) | 0.6868 | **0.6775** | [+0.0062, +0.0126] | 7/7 |

Both blends are now applied in live predictions (`handicap_blend_applied`
/ `totals_blend_applied` columns), gated per fixture on real market data
actually existing for that specific match and market -- exactly the same
"significant AND real data present" precondition the moneyline blend
uses, checked independently per market since real coverage differs
market to market (a bookmaker may post h2h before spreads, or totals
before either). Real spread/totals odds are aggregated across
bookmakers at the market's modal (most commonly quoted) line only --
not averaged across different lines, which would mix incomparable bets
(`prediction_ledger.load_live_spread_totals_odds`).

Tested via `tests/test_derived_markets.py` (pure scoreline-matrix math,
including the Asian Handicap quarter-line and whole-number-push
conventions) and `tests/test_spread_totals_blend_wiring.py` (blend
applies only to fixtures with real market data, mirroring
`test_market_blend_wiring.py`'s pattern for the moneyline blend).

## Limitations (read before trusting a number)

- **Correction (previously listed as a limitation, no longer accurate as
  of the season-level calibration work below):** both the match-level
  backtest (`backtest.py`) and the season-level calibration backtest
  (`season_calibration_backtest.py`) recompute the promoted-team
  offset -- and, now, its standard error -- using only data strictly
  before each validation season's first match, not the full dataset.
  Only the live 2026-27 production forecast uses the full
  2015/16-2025/26 window, which is correct there since there is no
  future data beyond it to leak. The backtest also does apply the
  promoted-team Dixon-Coles adjustment to validation-season promoted
  teams.
- **No market-odds baseline** is in the backtest comparison -- no
  historical odds source with sufficient, leakage-safe coverage was
  integrated in Phase 1 (football-data.co.uk's historical odds columns
  exist but were not wired into a baseline model this phase).
- **xG/PPDA/possession/big-chances are not available** for any
  historical season in the connected source, so the scoreline model is
  goals-only, not xG-informed.
- **Squad, transfer, injury, and lineup data are all unavailable**
  for 2026-27. **Market-odds data is a different story as of
  2026-08-21**: a validated model+market blend (see "Model+market
  blend" below) now does influence `home_win_prob_model_only`, for any
  fixture with real market odds available -- most of the season, that
  is no fixture at all (bookmakers post EPL markets only shortly before
  their own kickoff), so this mostly still reads as "model-only" in
  practice, but it is no longer categorically true. `data_quality_score`
  is discounted to reflect the squad/transfer/injury/lineup gaps (see
  `src/models/predict_all_matches.py`); it does not currently move for
  fixtures where the market blend was applied.
- **European/domestic-cup fixture congestion is not modeled** -- only
  Premier League fixtures are in scope, so `*_european_match_last_7_days`
  and `*_cup_match_last_7_days` are explicitly flagged unavailable
  rather than computed from an incomplete calendar.
- Dixon-Coles half-life and L2 regularization, and Elo K-factor and
  home-advantage, are now Optuna-tuned (Phase 2, see "Hyperparameter
  tuning" above); `rho` is still fit per-match by MLE, not separately
  tuned, and the tuning objective itself uses a single holdout season
  rather than a proper three-way train/tune/test split.

## Deferred to later phases (not built in Phase 1, 2, or 3)

Player-minutes/lineup-strength model and manager-tactical features
(no viable real source -- FBref/Understat were evaluated and rejected
on real ToS/technical grounds: understat.com's robots.txt is
`Disallow: /`, FBref's Terms of Use explicitly prohibit scraping and
explicitly prohibit building a website/tool from scraped data, and
FBref actively blocks bots via Cloudflare -- see
`config/data_sources.yaml`), and neural sequence models (skipped per
the spec's own "don't include for prestige" instruction -- ~4,000
historical matches is a small dataset for a deep sequence model;
classical/statistical models are used instead).

**Live market integration is connected, 2026-08-19**: a real, user-
supplied `ODDS_API_KEY` was added to a local gitignored `.env` (see
`.env.example`), never committed, never referenced from any
client-side file. `src/data_collection/collect_odds.py` -- already
built and tested against the real endpoint's no-key/invalid-key paths
-- now returns real data: 209 real bookmaker rows (15-21 bookmakers
per fixture) across the 10 gameweek-1 matches a market has been
posted for; the other 370 fixtures correctly stay the honest
`unavailable` sentinel until closer to their own kickoff.
`src/features/build_market_features.py`'s overround-removal and
log-odds-averaging math (previously unit-tested against synthetic
data only) now runs against this real feed via
`prediction_ledger.load_live_match_odds`, feeding both the prediction
ledger's `market_*` scoring baseline AND, as of 2026-08-21, the actual
published prediction for any fixture with real market data available
-- see "Model+market blend" below. This is a change from earlier in
this report (some passages above still describe market data as purely
a scoring baseline that never touches `home_win_prob_model_only` --
left as originally written rather than silently edited; superseded by
the section below, same append-only discipline as everywhere else in
this document).

**Injury/suspension data remains a genuine gap, re-checked
2026-08-19 with live evaluation, not just documentation review**:
API-Football is still unconfirmed for the same reason as before
(free-tier current-season coverage can't be verified without creating
a real account, which this environment does not do on its own).
PhysioRoom -- the best candidate free public injury table -- was
checked directly against its own Terms & Conditions: "You must not
reproduce, duplicate, copy or resell any part of the website or
content unless specifically authorized in writing" -- an explicit
reproduction prohibition, the same category of rejection as FBref
below, confirmed rather than assumed. Sky Sports, RotoWire, and
Squawka are standard ad-supported sports-media businesses in the same
category; no public, reproduction-permitting feed was found among
them either. Per this project's own rule ("if none exists, do NOT
proxy it"), team-level `unknown` sentinel rows remain the honest
state -- see `reports/epl_2026_27_data_audit.md`
"Known limitation: player availability."

**Squad/transfer market data remains a genuine gap, re-checked
2026-08-19**: Transfermarkt, the dominant free public source for
player market values and transfers, was checked directly rather than
assumed unusable -- its terms explicitly prohibit "mechanisms,
software or scripts" for automated access, and separately prohibit
"reproduction, inclusion in online services... or duplication on data
media of any kind, even in part" without prior written consent. This
is a more explicit, more direct prohibition than FBref's own rejected
terms, not merely the absence of an official API. No comparable free,
ToS-compliant alternative was found; this remains what the spec
already called for -- a licensed per-player transfer/market-value
data vendor.

Phase 2 completed: dashboard JSON (`src/dashboard/build_dashboard_json.py`),
the integrity audit (`src/run_integrity_audit.py`,
`reports/epl_2026_27_integrity_audit.md`), the model-risk audit, the
academic report, the portfolio summary, Optuna hyperparameter tuning,
and 10 additional tests (market-odds cleaning, injury/lineup
missingness flags, simulation table-rules).

Phase 3 completed: the stacked ensemble (`src/models/final_stacked_model.py`,
see "Stacked ensemble" above) -- of the 4 sub-models with real data
behind them, not the full 11-model ensemble the original spec
envisions, since the other 7 (player-minutes, squad-injury,
transfer-impact, market, tactical-style) have no connected data source
to stack -- and the weekly-update engine (`src/update_after_matchweek.py`,
see "Weekly-update engine" above), including
`test_completed_match_locking.py` and `test_weekly_update_versioning.py`,
verified against synthetic data since no real 2026-27 result exists
yet.

Phase 4 (external review corrections + data feed evaluation)
completed: a provenance audit confirmed no synthetic data has ever
reached `data/outputs/` or the real `data/raw/` files; a paired
bootstrap significance test replaced the ensemble's original raw
point-estimate comparison (see "Stacked ensemble" above -- this
demoted the ensemble from primary back to Dixon-Coles); the three
previously-deferred data feeds (player-minutes/xG/xA, live odds,
injuries) were each investigated on real terms/technical grounds
rather than left unexamined (see "Deferred to later phases" above);
and a real data-honesty bug was caught and fixed (an odds-collector
fallback path could label a non-real sentinel row with a real-looking
source name -- fixed, and generalized into a standing validator check
plus a regression test, `tests/test_odds_source_name_honesty.py`).

## Ethical note

This is a sports-analytics and forecasting project. Every number in
this system is a probability, not a guarantee. It is **not betting
advice**, and no output should be read as a promise about a real-money
outcome.
