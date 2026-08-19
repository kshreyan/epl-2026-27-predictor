# EPL 2026-27 Data Audit

Generated: 2026-08-18T03:17:40+00:00

This report accounts for every raw data file used by the pipeline: what is real and independently verifiable, and what is explicitly flagged as unavailable rather than fabricated. See `config/data_sources.yaml` for the full source registry.

## Connected real sources

- **football-data.co.uk**: EPL historical match results 2014/15-2025/26: goals, shots, cards, referee, historical Bet365 1X2 odds
  - URL pattern: https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv
- **fixturedownload.com**: 2026-27 EPL fixture list: all 380 matches, dates, kickoff times, venues
  - URL: https://fixturedownload.com/feed/json/epl-2026
  - Cross-checked against: Wikipedia '2026-27 Premier League' article (club list, promoted teams, season dates)

## Conditionally connected sources (collector built and tested, needs a user-supplied key)

- **the-odds-api.com**: Live EPL h2h (1X2) odds, free tier 500 credits/month, 1 credit per region per market
  - Terms evaluated: Explicitly permits use inside "websites, mobile apps, dashboards, analytical tools" as long as the data itself isn't resold as a standalone product -- fine for this project. Prohibits reselling/repackaging the raw data itself.
  - Key handling: ODDS_API_KEY env var, loaded from a local gitignored .env (see .env.example). Never hardcoded, never committed, never referenced from any client-side file (site/).
  - Status: Collector built and tested (sentinel path and API-error path both verified against the real endpoint). No real key is available in this environment (cannot self-service a signup) -- market_available remains False until a user supplies ODDS_API_KEY.

## Documented gaps (not fabricated, explicitly flagged)

- **live_bookmaker_odds**: no ODDS_API_KEY configured (see conditionally_connected_sources above -- collector is ready, key is not)
  - Affected files: data/raw/epl_2026_27_real_odds.csv, data/raw/epl_2026_27_outright_odds.csv
  - Mitigation: model-only mode used throughout; market_available=False on every row
- **current_injury_suspension_reports**: Evaluated API-Football (free tier: 100 req/day, all endpoints including /injuries, terms permit dashboard/app use). Its free-tier coverage of the CURRENT 2026-27 EPL season specifically is documented ambiguously ("free plans are limited in terms of available seasons") and cannot be confirmed without creating a real account and testing a real key -- something this environment cannot do on its own. Per the project's own rule ("if none exists, do NOT proxy it"), an unverified candidate is treated as not yet a connected source.
  - Affected files: data/raw/epl_2026_27_injury_suspension.csv
  - Mitigation: team-level availability_status=unknown sentinel rows; never treated as fully healthy. API-Football is documented as the leading candidate for a future collector, pending a human signing up and confirming current-season EPL injury coverage on the free tier.
- **player_minutes_xg_xa**: Evaluated the `soccerdata` package (FBref/Understat scrapers). Both underlying sources are unusable on real ToS/technical grounds, not just caution: understat.com's robots.txt is `Disallow: /` (blocks all automated access, verified directly); FBref's Terms of Use explicitly prohibit scraping AND explicitly prohibit "creat[ing] websites or tools based on data you scrape" -- directly contradicted by this project building a public dashboard -- and FBref actively blocks automated requests with a Cloudflare JS challenge (verified directly against robots.txt). No collector was built against either source.
  - Affected files: data/outputs/epl_2026_27_player_minutes_predictions.csv (never created), data/outputs/epl_2026_27_lineup_strength_by_match.csv (never created)
  - Mitigation: player-minutes/lineup-strength modeling remains fully deferred; no proxy or substitute data was used
- **squad_transfer_market_data**: requires a licensed per-player transfer/market-value data vendor
  - Affected files: data/raw/epl_2026_27_squads_transfers.csv
  - Mitigation: sentinel rows only; transfer-impact features deferred to a later phase
- **advanced_match_stats**: xG, PPDA, possession, big-chances, set-piece-xG are not published by football-data.co.uk (see player_minutes_xg_xa above for why FBref/Understat were not used as a substitute)
  - Affected files: data/raw/epl_historical_matches.csv
  - Mitigation: left blank per-row with an explicit notes flag; goal/shot-based models used instead of xG-based ones
- **clubelo.com_api**: unreachable from this environment (connection timeout) at collection time
  - Mitigation: Elo ratings computed in-house from real football-data.co.uk historical results instead (src/models/elo_model.py), so no external dependency is required

## Known limitation: player availability (injuries/suspensions)

No connected real source exists for current 2026-27 EPL injury/suspension data. `data/raw/epl_2026_27_injury_suspension.csv` is 20 team-level `availability_status=unknown` sentinel rows, not real reports -- per this project's rule, missing injury data is never treated as "fully healthy," and every prediction row sets `injury_data_available=False` rather than silently assuming a full-strength squad. API-Football was evaluated as a candidate (free tier: 100 requests/day, a dedicated `/injuries` endpoint, terms that permit dashboard/app use) but its free-tier coverage of the *current* season specifically could not be confirmed without creating a real account, which this pipeline cannot do on its own. This is a genuine, disclosed data gap, not a proxy or an estimate standing in for real data.

## Per-file summary

| File | Exists | Rows | Real rows | Flagged unavailable | Sources |
|---|---|---|---|---|---|
| epl_2026_27_fixtures.csv | yes | 380 | 380 | 0 | fixturedownload.com |
| epl_historical_matches.csv | yes | 4560 | 4560 | 0 | football-data.co.uk |
| epl_2026_27_squads_transfers.csv | yes | 20 | 0 | 20 | none_available |
| epl_2026_27_injury_suspension.csv | yes | 20 | 0 | 20 | none_available |
| epl_2026_27_real_odds.csv | yes | 380 | 0 | 380 | the-odds-api.com |
| epl_2026_27_match_odds.csv | yes | 380 | 10 | 370 | none_available (370 rows); ESPN/DraftKings, manual one-time snapshot, 2026-08-19 (10 rows, gameweek 1) |
| epl_2026_27_outright_odds.csv | yes | 140 | 20 | 120 | none_available (120 rows); sportsbettingdime.com/DraftKings, manual one-time snapshot, 2026-08-06 (20 rows) |

## Reading this table

- `epl_2026_27_fixtures.csv` and `epl_historical_matches.csv` should show **all rows real**, 0 flagged unavailable -- these are the two genuinely-connected real data sources.
- `epl_2026_27_squads_transfers.csv` and `epl_2026_27_injury_suspension.csv` should show **0 real rows, all rows flagged unavailable** -- these are honest sentinel files, not fabricated data.
- `epl_2026_27_outright_odds.csv` shows **20 real rows** (2026-08-18): a single manually-entered, de-vigged snapshot of title-winner and relegation odds from sportsbettingdime.com (DraftKings-averaged, dated 2026-08-06), one row per team for the 10 shortest-priced teams in each of those two markets. This is a one-time snapshot, not a live feed -- `src/data_collection/collect_outright_odds.py` preserves these `data_status=real_snapshot` rows on every re-run rather than overwriting them back to sentinels. The remaining 120 rows (other market types, and teams not listed on the source page for title/relegation) stay honestly flagged unavailable. See `reports/epl_2026_27_model_report.md` "Market comparison" for the model-vs-market analysis this enables.
- `epl_2026_27_real_odds.csv` shows 0 real rows **unless a real `ODDS_API_KEY` is configured** (see `.env.example`); the collector is built and tested against the real endpoint (both the no-key and invalid-key paths), but no key is available in this environment. If a key is ever added, expect real rows only for fixtures close enough to kickoff that a bookmaker has posted a market -- most of the 380 fixtures will still show unavailable at any given time.
- `epl_2026_27_match_odds.csv` shows **10 real rows** (2026-08-19): a manually-entered, de-vigged 1X2 snapshot for every real gameweek-1 fixture, from ESPN's odds pages (DraftKings Sportsbook), one page per match. Not a live feed and not confirmed to be the literal closing line (captured 2-3 days before kickoff, when the season had not yet started) -- `src/data_collection/collect_match_odds.py` preserves these `data_status=real_snapshot` rows on every re-run. `prediction_ledger.append_to_ledger` pulls them into the ledger's `market_*` fields, giving `score_weekly_results.py` a genuine market baseline for those 10 matches instead of the honest-but-empty "0 matches" state every other fixture still shows.
- Any prediction feature drawing on an unavailable file must set the corresponding `*_available=False` flag, which `src/models/predict_all_matches.py` does.
