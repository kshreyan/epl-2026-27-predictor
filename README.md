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

## Status: Phase 1 (v0)

This is a staged build. Phase 1 delivers a real, working, backtested
system covering the core pipeline; several parts of the full spec
(player-minutes modeling, live market integration, weekly in-season
updates, the full dashboard/report suite, hyperparameter tuning) are
explicitly deferred -- see `reports/epl_2026_27_model_report.md`
"Limitations" for the complete list and why.

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
simulation, and predicts all 380 real 2026-27 fixtures.

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
