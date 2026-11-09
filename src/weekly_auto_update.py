"""Closes the last real loop: after each real gameweek concludes,
fetch its actual results, lock them, refit, re-predict the rest of the
season (including next gameweek), score what just happened, and let
the gated recalibration process evaluate itself -- all without a human
pasting in a results CSV by hand.

This is the piece `run_pipeline.py --mode weekly_update` was always
missing: that mode already does everything AFTER a matchweek's results
are known (`update_after_matchweek.run_update`, which itself already
runs scoring and the gated recalibration check -- see
score_weekly_results.py and recalibration_gate.py), but something
still had to supply `--matchweek N --results path.csv` by hand. This
script is that missing piece, using a real, live results feed
(`fetch_live_results.py`, football-data.co.uk's live-updating
current-season file) instead of a manually-prepared file.

**A gameweek's real results lock incrementally, per match -- not
all-or-nothing.** Real fixtures within the same nominal gameweek
routinely finish on different real days (and, less often, a single
real fixture gets postponed weeks or months out -- confirmed directly:
La Liga's real 2026-10-10 Rayo Vallecano v Athletic Club was pushed to
2026-12-09). Earlier, this waited for EVERY one of a gameweek's real
fixtures before locking ANY of them -- one genuinely postponed match
then permanently blocked the other, already-decided real results in
that same round from ever locking or being scored (confirmed directly:
La Liga's real matchweek 8, stuck ~30 real days and still growing
before this fix). Now, whatever real results are actually available
for a gameweek get locked and scored immediately; whatever's still
missing simply stays `scheduled` and gets caught up on a later run
once its own real result appears -- `run_update()`'s own completed-
matches upsert is idempotent by match_id, so locking the same
gameweek more than once across separate runs is always safe.

Safe to run as often as you like (a scheduled GitHub Actions job runs
it daily): it is a real no-op -- no lock, no refit, no commit -- on
any day where no gameweek has a newly-available real result since the
last run.

Run: python -m src.weekly_auto_update
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection.fetch_live_results import fetch_all_live_results  # noqa: E402
from src.update_after_matchweek import DEFAULT_PATHS, run_update  # noqa: E402


def determine_matchweeks_with_new_results(
    fixtures_df: pd.DataFrame, live_results_df: pd.DataFrame, completed_df: pd.DataFrame,
) -> list[int]:
    """Matchweeks with at least one real result available that isn't
    locked yet, in chronological order (oldest first, so a multi-week
    gap since the last run gets caught up oldest-first the same way it
    always has -- this was never actually about requiring full
    completeness, just about processing order). A matchweek no longer
    needs EVERY one of its real fixtures to have a result before any of
    them can lock -- see this module's own docstring for the real
    incident that motivated this. `run_update` is called with whatever
    subset of a matchweek's real results is currently available; it
    locks exactly that subset (lock_completed_matches never requires a
    full matchweek) and leaves the rest `scheduled`."""
    locked_ids = set(completed_df["match_id"]) if not completed_df.empty else set()
    available_ids = set(live_results_df["match_id"])
    matchweeks_with_new_results = []
    for mw in sorted(fixtures_df["matchweek"].unique()):
        mw_ids = set(fixtures_df.loc[fixtures_df["matchweek"] == mw, "match_id"])
        newly_available = (mw_ids & available_ids) - locked_ids
        if newly_available:
            matchweeks_with_new_results.append(int(mw))
    return matchweeks_with_new_results


def run_auto_update(paths=DEFAULT_PATHS) -> list[dict]:
    """Returns one dict per matchweek actually processed this run (empty
    list on a no-op day). Each real matchweek with at least one newly-
    available real result gets its own run_update() call, in order, so
    scoring/recalibration correctly see one matchweek's worth of new
    data at a time, not several at once. A matchweek can be processed
    more than once across separate runs (a partial lock now, the rest
    once a postponed/late-reported fixture's own real result finally
    appears) -- always safe, see this module's own docstring."""
    fixtures_df = pd.read_csv(paths.fixtures)
    live_results_df = fetch_all_live_results(paths.fixtures, league_id=paths.league_id)
    completed_df = pd.read_csv(paths.completed_2627) if paths.completed_2627.exists() else pd.DataFrame(columns=["match_id"])

    matchweeks_with_new_results = determine_matchweeks_with_new_results(fixtures_df, live_results_df, completed_df)
    if not matchweeks_with_new_results:
        print("No matchweek with a newly-available real result found -- nothing to do.")
        return []

    processed = []
    for mw in matchweeks_with_new_results:
        mw_ids = set(fixtures_df.loc[fixtures_df["matchweek"] == mw, "match_id"])
        mw_results = live_results_df[live_results_df["match_id"].isin(mw_ids)]
        locked_ids_before = set(completed_df["match_id"]) if not completed_df.empty else set()
        n_still_missing = len(mw_ids) - len(mw_ids & set(mw_results["match_id"]))
        results_path = paths.weekly_dir / f"_auto_results_{paths.league_id}_matchweek_{mw:02d}.csv"
        paths.weekly_dir.mkdir(parents=True, exist_ok=True)
        mw_results.to_csv(results_path, index=False)

        partial_note = f" ({n_still_missing} real fixture(s) in this matchweek still have no result yet)" if n_still_missing else ""
        print(f"\n{'=' * 70}\nMatchweek {mw}: locking {len(mw_results)} real result(s) total available for "
              f"this matchweek{partial_note}, re-predicting the rest of the season.\n{'=' * 70}")
        result = run_update(matchweek=mw, results_path=results_path, paths=paths)
        n_newly_locked = len(set(mw_results["match_id"]) - locked_ids_before)
        processed.append({"matchweek": mw, "n_results": n_newly_locked, "run_id": result["run_id"]})

        # Refresh completed_df for the next iteration's lock check.
        completed_df = pd.read_csv(paths.completed_2627)

    from src.dashboard.build_dashboard_json import main as build_dashboard_json
    build_dashboard_json()  # rebuilds every configured league's dashboard JSON, not just this one

    return processed


if __name__ == "__main__":
    import argparse
    from src.update_after_matchweek import WeeklyUpdatePaths
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="epl", dest="league_id")
    _args = _parser.parse_args()
    processed = run_auto_update(paths=WeeklyUpdatePaths.for_league(_args.league_id))
    if processed:
        print(f"\nProcessed {len(processed)} matchweek(s): {[p['matchweek'] for p in processed]}")
