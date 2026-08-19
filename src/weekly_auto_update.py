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

**A gameweek is "concluded" only when EVERY one of its real fixtures
has a real result available** -- not the first result, not most of
them. Postponements/rearrangements mean a gameweek's matches don't
always all finish on the same day; this waits for all of them rather
than guessing which ones will be rescheduled soon versus much later.

Safe to run as often as you like (a scheduled GitHub Actions job runs
it daily): it is a real no-op -- no lock, no refit, no commit -- on
any day where no new gameweek has fully concluded since the last run.

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


def determine_newly_complete_matchweeks(
    fixtures_df: pd.DataFrame, live_results_df: pd.DataFrame, completed_df: pd.DataFrame,
) -> list[int]:
    """Matchweeks where every real fixture now has a real result
    available AND that matchweek is not already fully locked, in
    chronological order (so a multi-week gap since the last run gets
    caught up one matchweek at a time, oldest first -- required, since
    `run_update` locks and refits using ALL completed-so-far data, and
    each matchweek's own pre-kickoff prediction must reflect only the
    matchweeks strictly before it, not ones from later in the gap)."""
    locked_ids = set(completed_df["match_id"]) if not completed_df.empty else set()
    available_ids = set(live_results_df["match_id"])
    newly_complete = []
    for mw in sorted(fixtures_df["matchweek"].unique()):
        mw_ids = set(fixtures_df.loc[fixtures_df["matchweek"] == mw, "match_id"])
        if mw_ids and mw_ids <= locked_ids:
            continue  # already fully locked
        if mw_ids and mw_ids <= available_ids:
            newly_complete.append(int(mw))
    return newly_complete


def run_auto_update(paths=DEFAULT_PATHS) -> list[dict]:
    """Returns one dict per matchweek actually processed this run (empty
    list on a no-op day). Each real matchweek gets its own run_update()
    call, in order, so scoring/recalibration correctly see one
    matchweek's worth of new data at a time, not several at once."""
    fixtures_df = pd.read_csv(paths.fixtures)
    live_results_df = fetch_all_live_results(paths.fixtures)
    completed_df = pd.read_csv(paths.completed_2627) if paths.completed_2627.exists() else pd.DataFrame(columns=["match_id"])

    newly_complete = determine_newly_complete_matchweeks(fixtures_df, live_results_df, completed_df)
    if not newly_complete:
        print("No newly-concluded matchweek found -- nothing to do.")
        return []

    processed = []
    for mw in newly_complete:
        mw_ids = set(fixtures_df.loc[fixtures_df["matchweek"] == mw, "match_id"])
        mw_results = live_results_df[live_results_df["match_id"].isin(mw_ids)]
        results_path = paths.weekly_dir / f"_auto_results_matchweek_{mw:02d}.csv"
        paths.weekly_dir.mkdir(parents=True, exist_ok=True)
        mw_results.to_csv(results_path, index=False)

        print(f"\n{'=' * 70}\nMatchweek {mw} concluded -- locking {len(mw_results)} real result(s) "
              f"and re-predicting the rest of the season.\n{'=' * 70}")
        result = run_update(matchweek=mw, results_path=results_path, paths=paths)
        processed.append({"matchweek": mw, "n_results": len(mw_results), "run_id": result["run_id"]})

        # Refresh completed_df for the next iteration's lock check.
        completed_df = pd.read_csv(paths.completed_2627)

    from src.dashboard.build_dashboard_json import main as build_dashboard_json
    build_dashboard_json()

    return processed


if __name__ == "__main__":
    processed = run_auto_update()
    if processed:
        print(f"\nProcessed {len(processed)} matchweek(s): {[p['matchweek'] for p in processed]}")
