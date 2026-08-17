# EPL 2026-27 Data Audit

Generated: 2026-08-17T23:11:24+00:00

This report accounts for every raw data file used by the pipeline: what is real and independently verifiable, and what is explicitly flagged as unavailable rather than fabricated. See `config/data_sources.yaml` for the full source registry.

## Connected real sources

- **football-data.co.uk**: EPL historical match results 2014/15-2025/26: goals, shots, cards, referee, historical Bet365 1X2 odds
  - URL pattern: https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv
- **fixturedownload.com**: 2026-27 EPL fixture list: all 380 matches, dates, kickoff times, venues
  - URL: https://fixturedownload.com/feed/json/epl-2026
  - Cross-checked against: Wikipedia '2026-27 Premier League' article (club list, promoted teams, season dates)

## Documented gaps (not fabricated, explicitly flagged)

- **live_bookmaker_odds**: requires a paid odds-API subscription; not available in this environment
  - Affected files: data/raw/epl_2026_27_real_odds.csv, data/raw/epl_2026_27_outright_odds.csv
  - Mitigation: model-only mode used throughout Phase 1; market_available=False on every row
- **current_injury_suspension_reports**: requires a live, continuously-updated injury-news feed
  - Affected files: data/raw/epl_2026_27_injury_suspension.csv
  - Mitigation: team-level availability_status=unknown sentinel rows; never treated as fully healthy
- **squad_transfer_market_data**: requires a licensed per-player transfer/market-value data vendor
  - Affected files: data/raw/epl_2026_27_squads_transfers.csv
  - Mitigation: sentinel rows only; transfer-impact features deferred to a later phase
- **advanced_match_stats**: xG, PPDA, possession, big-chances, set-piece-xG are not published by football-data.co.uk
  - Affected files: data/raw/epl_historical_matches.csv
  - Mitigation: left blank per-row with an explicit notes flag; goal/shot-based models used instead of xG-based ones
- **clubelo.com_api**: unreachable from this environment (connection timeout) at collection time
  - Mitigation: Elo ratings computed in-house from real football-data.co.uk historical results instead (src/models/elo_model.py), so no external dependency is required

## Per-file summary

| File | Exists | Rows | Real rows | Flagged unavailable | Sources |
|---|---|---|---|---|---|
| epl_2026_27_fixtures.csv | yes | 380 | 380 | 0 | fixturedownload.com |
| epl_historical_matches.csv | yes | 4560 | 4560 | 0 | football-data.co.uk |
| epl_2026_27_squads_transfers.csv | yes | 20 | 0 | 20 | none_available |
| epl_2026_27_injury_suspension.csv | yes | 20 | 0 | 20 | none_available |
| epl_2026_27_real_odds.csv | yes | 380 | 0 | 380 | none_available |
| epl_2026_27_outright_odds.csv | yes | 140 | 0 | 140 | none_available |

## Reading this table

- `epl_2026_27_fixtures.csv` and `epl_historical_matches.csv` should show **all rows real**, 0 flagged unavailable -- these are the two genuinely-connected real data sources.
- `epl_2026_27_squads_transfers.csv`, `epl_2026_27_injury_suspension.csv`, `epl_2026_27_real_odds.csv`, and `epl_2026_27_outright_odds.csv` should show **0 real rows, all rows flagged unavailable** -- these are honest sentinel files, not fabricated data. Any prediction feature drawing on them must set the corresponding `*_available=False` flag, which `src/models/predict_all_matches.py` does.
