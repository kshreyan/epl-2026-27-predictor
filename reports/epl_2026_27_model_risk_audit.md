# EPL 2026-27 Model Risk Audit

Generated as part of Phase 2. This audit exists to say plainly where
this system is **less reliable**, not to reassure. Read it before
trusting any specific number.

## data_reliability

**Fixtures and historical results: high.** Both are real, sourced,
timestamped, and cross-checked (fixtures against Wikipedia; historical
results are the standard football-data.co.uk dataset widely used in
football-analytics research). **Everything else: not applicable --
there is no data to be reliable or unreliable, because no feed is
connected** (odds, injuries, transfers, squad values). Predictions are
model-only by construction, not degraded-market predictions.

## missing_data_risk

Every 2026-27 match prediction is missing squad, injury, lineup,
transfer, and market-odds context. `data_quality_score` is capped at
0.20 for every 2026-27 prediction row for exactly this reason (see
`src/models/predict_all_matches.py`). A team missing a key player, a
new signing not yet reflected anywhere, or a tactical change from a
new manager will not move this model's number at all until those data
sources exist. Treat every prediction as "what a goals-only model
thinks, with no squad-news adjustment," not as a complete forecast.

## fixture_rescheduling_risk

The 2026-27 fixture list reflects the originally-published schedule.
Premier League broadcasters routinely move matches (different date/
kickoff time) once TV picks are announced, especially from
matchweek ~10 onward. `data/raw/epl_2026_27_fixtures.csv` rows are
marked `data_status=scheduled_provisional` for exactly this reason --
re-collect (`src/data_collection/collect_fixtures.py`) close to any
matchweek before treating `kickoff_utc` as final.

## odds_leakage_risk

None currently possible: no odds of any kind (opening/current/closing)
are connected. This becomes a real risk the moment a live feed is
wired in, and the project's rules (spec section 2/17) are explicit
that closing odds must never be used before a real prediction
timestamp -- enforce this at the collector layer when that work
happens, not just in downstream code.

## injury_source_reliability

Not applicable -- no injury source is connected. Every 2026-27
prediction has `injury_data_available=False`.

## lineup_uncertainty

Maximal and unaddressed. No expected-lineup or confirmed-lineup logic
exists yet (deferred to a later phase). Every prediction implicitly
assumes "whatever XI each team's attack/defense parameters represent
on historical average," which washes out any single-match rotation,
injury absence, or tactical surprise.

## model_overfitting_risk

**Moderate, monitored.** The Dixon-Coles model has ~74 free parameters
(36 teams x attack+defense, plus home advantage and rho) fit on 4,560
historical matches -- a reasonable parameter-to-data ratio for this
model family, and the L2 ridge penalty (tuned to 0.123, see
`reports/epl_hyperparameter_tuning_report.md`) exists specifically to
control this. The real backtest result (Dixon-Coles beating three
simpler baselines on 2,660 held-out matches, not just beating a naive
guess) is the actual evidence against overfitting; a model that had
overfit its 4,560 training matches would typically *lose* to the
simpler baselines out of sample, which it does not.

**Where this risk is real:** the hyperparameter tuning objective
itself uses a *single* held-out season (2025/26) rather than a proper
train/tune/test three-way split, so the tuned half_life/l2_reg/
k_factor values could be mildly overfit to that one season's specific
character rather than the league's long-run behavior. See "calibration
limits" below and `reports/epl_hyperparameter_tuning_report.md`.

## promoted_team_uncertainty

**High, and deliberately so.** Coventry City has zero matches in the
historical dataset (last top-flight appearance predates our
2014/15-2025/26 window); the Laplace-approximation uncertainty band on
their attack/defense parameters is the widest of any club in the
league by a large margin (see
`data/outputs/epl_2026_27_dynamic_team_strength.csv`,
`uncertainty_score` column). Hull City's most recent EPL data is 9
years stale; Ipswich Town's is 1 year old and therefore the most
reliable of the three. All three promoted clubs' predictions should be
read as considerably less certain than an established club's, even
though the model produces a specific number for each match.

## new_manager_uncertainty

Not modeled. No manager-identity or tenure data source is connected
(spec section 13's manager/tactical feature layer is deferred). A club
with a brand-new manager and a genuinely different tactical approach
this season will be predicted purely from last season's goals data,
with no adjustment.

## major_transfer_uncertainty

Not modeled for the same reason -- no transfer data source is
connected. A club that sold its top scorer or bought a new one will
not see that reflected until enough 2026-27 matches accumulate to move
the (currently nonexistent, preseason-only) team-strength estimate.

## early_season_uncertainty

Real and expected. Every 2026-27 prediction in this system is a
**preseason** prediction (today, 2026-08-18, is before kickoff on
2026-08-21) -- there is zero 2026-27 form signal in any number here.
Early-season matches, especially for the three promoted clubs and any
club with unusually large squad turnover, carry materially more
uncertainty than the same fixture would in November. The weekly-update
engine (a later phase) is what's supposed to narrow this as real
matches are played; it does not exist yet.

## market_dependency

None -- by design, this system is model-only in Phase 1/2. This
avoids one failure mode (blindly copying market consensus) at the cost
of another (missing whatever information a real market-maker has that
this model doesn't, e.g. real injury news). Neither failure mode has
been eliminated, only chosen between, until market integration exists.

## calibration_limits

Isotonic calibration was fit on the same 2,660-match backtest window
used to report headline metrics (log loss, ECE), rather than a
separate held-out calibration fold -- documented in
`data/outputs/epl_2026_27_calibration_report.md` "Limitations". This
can modestly overstate calibration quality. The reported ECE (0.0084)
should be read as "well-calibrated on this backtest," not as a
guaranteed property of future predictions.

## exact_score_uncertainty

Exact-scoreline prediction is inherently high-variance: even a
well-calibrated model with 11.2% real backtest exact-score accuracy
(see `reports/epl_model_selection_report.md`) will be "wrong" on the
literal scoreline in roughly 9 matches out of 10. The `predicted_score`
field is the single most likely outcome, not an expectation of being
usually correct -- `top_10_scorelines_model_only_json` and the win/
draw/loss probabilities are the more honest way to read any match.

## simulation_uncertainty

The 250,000-run Monte Carlo simulation holds team strength **static**
for the entire simulated season (see
`reports/epl_2026_27_model_report.md`) -- no simulated path models a
team improving or declining mid-season, which real seasons obviously
do. This means the simulation's position-distribution spread is likely
an *underestimate* of the true uncertainty in where a club finishes,
since it's missing a real source of season-to-season variance (form
swings, injuries, managerial changes happening in-season). Head-to-head
tie-breaking is also not implemented (alphabetical fallback instead,
see `config/simulation_config.yaml`) -- this only matters for the rare
case of a title race, European qualification spot, or relegation
battle coming down to a tie that head-to-head would have resolved
differently.

## dashboard_interpretation_risk

No dashboard exists yet in Phase 1/2 (deferred). When it is built, the
single highest-risk misinterpretation to guard against in its design
is presenting `predicted_score` as a confident forecast rather than
the single most likely cell of a wide probability distribution --
every scoreline-related UI element should surface `top_10_scorelines`
and the entropy/confidence fields alongside it, never the predicted
score alone.

---

**Overall read:** the core statistical engine (Elo + Dixon-Coles,
backtested and tuned on real data) is on reasonably solid footing. The
much bigger source of risk in this system right now is not the model,
it's everything the model *doesn't know* -- squad news, injuries,
transfers, lineups, and markets -- none of which is connected yet.
Treat every 2026-27 number as "what a real, historically-validated
goals model thinks with zero current-season information," not as a
complete football forecast.
