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

**Repository:** https://github.com/kshreyan/epl-2026-27-predictor

**Live dashboard:** https://kshreyan.github.io/epl-2026-27-predictor/
(live once Pages is enabled with source "GitHub Actions" in repo
Settings and `.github/workflows/deploy.yml` has run once).

## Backtest headline numbers (real, not illustrative)

Rolling-origin backtest, 2019/20-2025/26, 2,660 real historical
matches, no random splitting:

| Model | Log loss | Exact-score accuracy |
|---|---|---|
| **Dixon-Coles (primary model)** | **0.9865** | **11.2%** |
| Elo-only baseline | 0.9931 | -- |
| Simple Poisson baseline | 1.0178 | -- |
| Previous-season-table baseline | 1.2100 | -- |

Isotonic calibration brings top-class Expected Calibration Error to
**0.0114**. A stacked ensemble of the four models above was evaluated
with a paired bootstrap (10,000 resamples) and demoted: its apparent
edge (log loss 0.9834) was not statistically significant (95% CI
[-0.0021, +0.0087], wins only 3/7 backtest seasons) -- Dixon-Coles
alone is the primary model. Full detail:
`reports/epl_2026_27_ensemble_report.md`,
`reports/epl_model_selection_report.md`.

## Known data gaps

- **Player-minutes/xG/xA**: rejected. `understat.com`'s robots.txt
  disallows all automated access; `FBref`'s Terms of Use explicitly
  prohibit scraping and explicitly prohibit building a website/tool
  from scraped data (this project builds a public dashboard); FBref
  also actively blocks bots via Cloudflare.
- ~~Live 1X2 odds~~ **connected, 2026-08-21** (`src/data_collection/collect_odds.py`,
  The Odds API, real `ODDS_API_KEY` configured -- both locally and as a
  GitHub Actions secret, refreshed automatically every day). Real
  market data now also feeds a validated model+market blend into live
  predictions for any fixture it covers (see
  `reports/epl_2026_27_model_report.md` "Model+market blend") -- a
  paired-bootstrap-tested edge (log loss 0.9865 -> 0.9717 vs Dixon-Coles
  alone, 7/7 backtest seasons), not an assumption that blending helps.
- ~~Spread/totals/BTTS predictions~~ **added, 2026-08-25**: every fixture
  now also gets a both-teams-to-score, Asian Handicap (spread), and
  Over/Under 2.5 (totals) prediction, with real market data connected
  for spread and totals (also via The Odds API and football-data.co.uk)
  and each blended in only where independently validated -- see
  `reports/epl_2026_27_model_report.md` "BTTS, spread, and totals
  predictions". BTTS has no real market source anywhere (checked
  directly: unsupported by the live odds API for this sport, no column
  in the historical data either) and stays model-only.
- **Injuries/suspensions**: no free source with confirmable current-season
  EPL coverage. Left as an honest `unknown` sentinel, never proxied.

See `reports/epl_2026_27_data_audit.md` "Known limitation" for the full
writeup.

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

**This now happens automatically.** `.github/workflows/weekly_update.yml`
runs daily: refreshes live match odds (`ODDS_API_KEY` GitHub Actions
secret), fetches real completed 2026-27 results
(`src/data_collection/fetch_live_results.py`, football-data.co.uk's
live-updating current-season file, no key needed for this part), locks
any gameweek that has newly and fully concluded, refits, re-predicts
the rest of the season (including next gameweek), scores what just
happened, lets the gated recalibration process evaluate itself (150
real matches minimum, paired-bootstrap 95% CI required to promote a
challenger -- never automatic on a small sample, see
`reports/epl_2026_27_model_report.md` "Recalibration gate"), and
commits the result -- a genuine no-op (beyond the odds refresh) on any
day no gameweek concluded. That commit triggers `deploy.yml` to
redeploy the dashboard.

To do the same thing manually for one matchweek (e.g. to test a
results file before the automation would pick it up):

```bash
python run_pipeline.py --season 2026-27 --mode weekly_update --matchweek 1 --results path/to/results.csv
```

`results.csv` needs columns `match_id,home_goals,away_goals,source_name,source_timestamp`.

## Key outputs

- `data/outputs/epl_2026_27_match_predictions.csv` -- every fixture: predicted score, top-10 scorelines, 1X2/BTTS/spread/totals probabilities, confidence, upset risk
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
`model_registry/`, and `data/versions/`. `site/` is the static
dashboard (Vite + React + TypeScript + Tailwind + Recharts) that reads
`data/outputs/dashboard/*.json` -- no backend, no runtime API calls,
deployed to GitHub Pages by `.github/workflows/deploy.yml` on every
push to `main`. See `site/README.md` for local dev instructions.
