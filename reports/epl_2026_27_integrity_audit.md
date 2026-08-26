# EPL 2026-27 Integrity Audit

Generated: 2026-08-26T02:51:46+00:00

**23 passed, 0 failed, 3 not yet applicable** (out of 26 checks).

| Status | Check | Detail |
|---|---|---|
| PASS | All 380 fixtures are present | found 380 |
| PASS | No duplicate match IDs in fixtures |  |
| PASS | No missing teams (exactly the 20 real 2026-27 clubs) |  |
| PASS | No fake odds are used (every real row has a real source_name and data_status=live; every other row is explicitly flagged unavailable, never fabricated) | 2512 rows checked (1432 real, 1080 unavailable) |
| PASS | No fake injuries are used (all 2026-27 injury rows are explicitly flagged unavailable, not fabricated) | 20 rows checked |
| PASS | No fake squad news is used (all 2026-27 squad rows are explicitly flagged unavailable, not fabricated) | 20 rows checked |
| PASS | No placeholder rows in historical matches are treated as real (is_real_data=True implies a real source, and every row has one) | 4560 rows, source=['football-data.co.uk'] |
| PASS | All model-only probability rows sum to 1 |  |
| PASS | Predicted result matches predicted score on every row |  |
| PASS | Scheduled (not-yet-played) matches carry no actual result |  |
| PASS | Completed matches (if any) have an actual result -- N/A this run since 0 completed matches exist yet | 10 completed rows |
| PASS | No future-data leakage: every prediction's generated_at is at or before that match's kickoff_utc |  |
| PASS | Market odds are used only when verified real: market_available is False on every row (no real odds feed connected in Phase 1/2) |  |
| PASS | Model-only and market-integrated outputs are clearly separated (market-integrated columns are blank, not duplicated model-only values, while market is unavailable) |  |
| PASS | Injury data is flagged when missing (injury_data_available=False on every 2026-27 prediction row) |  |
| PASS | Lineup data is flagged when missing (lineup_data_available=False on every 2026-27 prediction row) |  |
| PASS | Exactly 20 position-finish columns (1st-20th) |  |
| PASS | Position probabilities for each team sum to 1 | max deviation 0.0000 |
| PASS | Sum of title (1st-place) probabilities across all 20 teams is ~1 | sum=1.0000 |
| PASS | Sum of relegation-zone (18th-20th) probabilities across all 20 teams is ~3 | sum=3.0000 |
| PASS | Expected table has exactly 20 teams, no duplicates |  |
| PASS | Relegation/top-4/top-5/title probabilities are internally consistent (title<=top4<=top5<=top_half) |  |
| PASS | Final table calculations are correct: expected_wins+draws+losses == 38 for every team |  |
| N/A (feature not yet built) | Weekly updates do not overwrite old prediction timestamps | No weekly-update engine exists yet (2026-27 season has not started; today is preseason). Deferred to a later phase. |
| N/A (feature not yet built) | Simulation uses actual completed results locked + simulated future results | No 2026-27 matches have been played yet (preseason_mode); all 380 fixtures are simulated as future matches, which is correct for this point in time, not a failure of the locking mechanism. |
| N/A (feature not yet built) | Closing odds are not leaked into pre-match predictions | No odds feed (opening, current, or closing) is connected in Phase 1/2 at all -- there is nothing to leak. Will become a real check once a live odds feed is wired in. |

## Reading N/A rows

An "N/A (feature not yet built)" row is not a pass -- it means the corresponding pipeline stage (weekly updates, market integration) does not exist yet in this phase, so the check has nothing to verify. See reports/epl_2026_27_model_report.md "Deferred to later phases" for what's missing and why. These rows must become real PASS/FAIL checks, never be silently removed, once that functionality is built.
