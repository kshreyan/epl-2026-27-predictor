# Premier League 2026/27 Prediction System

A probabilistic forecasting system for the English Premier League
2026/27 season: match-level scoreline distributions, result
probabilities, and a full-season Monte Carlo simulation (title, top-4,
top-5, relegation probabilities, and a full 1st-20th position
distribution for every club).

**This is a forecasting and sports-analytics project, not betting
advice.** Every output is a probability, not a guarantee. See
`reports/epl_2026_27_model_risk_audit.md` for where the model is least
reliable.

## Status: Phases 1-4

This is a staged build. Phases 1-3 deliver a real, working, backtested
core pipeline, Optuna-tuned hyperparameters, a stacked ensemble, the
full report/audit suite, dashboard JSON, and a weekly-update engine
(verified against synthetic data since the real season hasn't started
yet). Phase 4 added a paired-bootstrap significance test that found
the ensemble's apparent edge over Dixon-Coles was not statistically
distinguishable from noise (95% CI straddles zero, wins only 3/7
backtest seasons) -- Dixon-Coles alone is the primary model -- plus a
provenance audit and a real investigation of the three previously-
deferred data feeds (player-minutes/xG/xA: rejected on real terms/
technical grounds; live odds: built and tested, needs a user-supplied
API key; injuries: no viable free source confirmed, left as an honest
gap). See `reports/epl_2026_27_data_audit.md` "Known limitation."
Player-minutes modeling, injury/transfer features, and live market
integration remain explicitly deferred --
all blocked on data sources with no connection in this environment,
not on missing effort. See
`reports/epl_2026_27_model_report.md` "Deferred to later phases" for
the complete list and why.

## Data honesty

Every raw data file is either **real** (fetched from a named, citable
source, with a `source_name`/`source_timestamp` on every row) or an
**explicitly flagged sentinel** (`is_real_data=False`,
`data_status=unavailable`) when no verified source is connected. Never
both, never fabricated. See `reports/epl_2026_27_data_audit.md` for
the full accounting and `config/data_sources.yaml` for the source
registry.

Real sources used: `football-data.co.uk` (EPL historical results
2014/15-2025/26) and `fixturedownload.com` (the 380 real 2026-27
fixtures, cross-checked against Wikipedia).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run_pipeline.py --season 2026-27 --mode preseason
pytest tests/
```

This collects real data, validates it, builds features, runs a
rolling-origin backtest on 7 real historical seasons, calibrates
probabilities, runs a 250,000-simulation Monte Carlo season
simulation, and predicts all 380 real 2026-27 fixtures (via the
stacked ensemble only when a paired-bootstrap significance test says
its edge over Dixon-Coles alone is real, checked fresh every run --
currently it isn't, so Dixon-Coles alone is used; see
`reports/epl_2026_27_ensemble_report.md`).

Once the season starts, lock a matchweek's real results and re-predict
the rest of the season:

```bash
python run_pipeline.py --season 2026-27 --mode weekly_update --matchweek 1 --results path/to/results.csv
```

`results.csv` needs columns `match_id,home_goals,away_goals,source_name,source_timestamp`.

## Key outputs

- `data/outputs/epl_2026_27_match_predictions.csv` -- every fixture: predicted score, top-10 scorelines, 1X2 probabilities, confidence, upset risk
- `data/outputs/epl_2026_27_expected_table.csv` -- expected final table with uncertainty bands
- `data/outputs/epl_2026_27_position_distribution.csv` -- full 1st-20th finish probability for every club
- `data/outputs/epl_2026_27_title_race.csv`, `_top4_probabilities.csv`, `_relegation_probabilities.csv`
- `data/outputs/epl_backtest_model_comparison.csv` -- how the model performs against honest baselines on real history
- `reports/epl_2026_27_data_audit.md` -- what's real vs. flagged
- `reports/epl_2026_27_model_report.md` -- methodology and limitations

## Project layout

See `reports/epl_2026_27_model_report.md` for full methodology.
Production code lives in `src/`; notebooks (if any) are exploration
only. Every model run is versioned in `experiments/`,
`model_registry/`, and `data/versions/`.
