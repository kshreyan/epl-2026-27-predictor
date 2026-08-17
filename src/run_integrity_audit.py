"""Integrity audit: automated checks the project spec requires to pass
before the system can be considered trustworthy (spec section 33).

Each check is (a) run programmatically here and (b) mirrored, where
feasible, by a real pytest test in tests/ -- this script is the single
place that runs the *complete* checklist end-to-end and writes a
human-readable pass/fail report. A handful of checks are marked
"not yet applicable" rather than pass/fail: they test functionality
(weekly updates, market-integrated predictions, live-completed-match
locking) that Phase 1/2 hasn't built yet, per
reports/epl_2026_27_model_report.md "Deferred to later phases". Marking
something "not applicable" here is itself an honesty commitment: it
must be flipped to a real pass/fail check, never silently deleted, the
moment the corresponding feature exists.

Run: python src/run_integrity_audit.py
Exits non-zero if any applicable check fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

RAW = REPO_ROOT / "data" / "raw"
OUT = REPO_ROOT / "data" / "outputs"
OUT_REPORT = REPO_ROOT / "reports" / "epl_2026_27_integrity_audit.md"

results: list[dict] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def not_applicable(name: str, detail: str) -> None:
    results.append({"check": name, "status": "N/A (feature not yet built)", "detail": detail})


def run_checks() -> None:
    fixtures = pd.read_csv(RAW / "epl_2026_27_fixtures.csv")
    check("All 380 fixtures are present", len(fixtures) == 380, f"found {len(fixtures)}")
    check("No duplicate match IDs in fixtures", fixtures["match_id"].duplicated().sum() == 0)
    check(
        "No missing teams (exactly the 20 real 2026-27 clubs)",
        set(fixtures["home_team"]) | set(fixtures["away_team"]) == set(EPL_2026_27_CLUBS),
    )

    odds = pd.read_csv(RAW / "epl_2026_27_real_odds.csv")
    check(
        "No fake odds are used (all 2026-27 odds rows are explicitly flagged unavailable, not fabricated)",
        bool((odds["is_real_data"] == False).all() and (odds["data_status"] == "unavailable").all()),  # noqa: E712
        f"{len(odds)} rows checked",
    )

    injuries = pd.read_csv(RAW / "epl_2026_27_injury_suspension.csv")
    check(
        "No fake injuries are used (all 2026-27 injury rows are explicitly flagged unavailable, not fabricated)",
        bool((injuries["is_real_data"] == False).all() and (injuries["availability_status"] == "unknown").all()),  # noqa: E712
        f"{len(injuries)} rows checked",
    )

    squads = pd.read_csv(RAW / "epl_2026_27_squads_transfers.csv")
    check(
        "No fake squad news is used (all 2026-27 squad rows are explicitly flagged unavailable, not fabricated)",
        bool((squads["is_real_data"] == False).all() and (squads["data_status"] == "unavailable").all()),  # noqa: E712
        f"{len(squads)} rows checked",
    )

    historical = pd.read_csv(RAW / "epl_historical_matches.csv")
    check(
        "No placeholder rows in historical matches are treated as real (is_real_data=True implies a real source, and every row has one)",
        bool((historical["is_real_data"] == True).all() and historical["source_name"].notna().all()),  # noqa: E712
        f"{len(historical)} rows, source={historical['source_name'].unique().tolist()}",
    )

    predictions_path = OUT / "epl_2026_27_match_predictions.csv"
    if not predictions_path.exists():
        check("Match predictions file exists", False, "run src/models/predict_all_matches.py first")
    else:
        preds = pd.read_csv(predictions_path, parse_dates=["generated_at", "kickoff_utc"], date_format="ISO8601")
        prob_sums = preds["home_win_prob_model_only"] + preds["draw_prob_model_only"] + preds["away_win_prob_model_only"]
        check("All model-only probability rows sum to 1", bool((prob_sums.sub(1.0).abs() < 1e-3).all()))

        def result_matches_score(row):
            hg, ag = row["predicted_score_model_only"].split("-")
            hg, ag = int(hg), int(ag)
            expected = "home_win" if hg > ag else ("away_win" if hg < ag else "draw")
            return row["predicted_result_model_only"] == expected

        check("Predicted result matches predicted score on every row", bool(preds.apply(result_matches_score, axis=1).all()))

        scheduled = preds[preds["status"] == "scheduled"]
        check(
            "Scheduled (not-yet-played) matches carry no actual result",
            bool(scheduled["actual_home_goals"].isna().all() and scheduled["actual_away_goals"].isna().all()),
        )
        completed = preds[preds["status"] == "completed"]
        check(
            "Completed matches (if any) have an actual result -- N/A this run since 0 completed matches exist yet",
            True if completed.empty else bool(completed["actual_home_goals"].notna().all()),
            f"{len(completed)} completed rows",
        )

        check(
            "No future-data leakage: every prediction's generated_at is at or before that match's kickoff_utc",
            bool((preds["generated_at"] <= preds["kickoff_utc"]).all()),
        )
        check(
            "Market odds are used only when verified real: market_available is False on every row (no real odds feed connected in Phase 1/2)",
            bool((preds["market_available"] == False).all()),  # noqa: E712
        )
        check(
            "Model-only and market-integrated outputs are clearly separated (market-integrated columns are blank, not duplicated model-only values, while market is unavailable)",
            bool((preds["predicted_score_market_integrated"].isna() | (preds["predicted_score_market_integrated"] == "")).all()),
        )
        check(
            "Injury data is flagged when missing (injury_data_available=False on every 2026-27 prediction row)",
            bool((preds["injury_data_available"] == False).all()),  # noqa: E712
        )
        check(
            "Lineup data is flagged when missing (lineup_data_available=False on every 2026-27 prediction row)",
            bool((preds["lineup_data_available"] == False).all()),  # noqa: E712
        )

    pos_dist_path = OUT / "epl_2026_27_position_distribution.csv"
    expected_table_path = OUT / "epl_2026_27_expected_table.csv"
    if not pos_dist_path.exists() or not expected_table_path.exists():
        check("Simulation output files exist", False, "run src/simulation/simulate_full_season.py first")
    else:
        pos_dist = pd.read_csv(pos_dist_path)
        finish_cols = [c for c in pos_dist.columns if c.startswith("finish_")]
        check("Exactly 20 position-finish columns (1st-20th)", len(finish_cols) == 20)
        row_sums = pos_dist.set_index("team")[finish_cols].sum(axis=1)
        check("Position probabilities for each team sum to 1", bool((row_sums.sub(1.0).abs() < 0.02).all()), f"max deviation {row_sums.sub(1.0).abs().max():.4f}")

        title_col_sum = pos_dist["finish_1_probability"].sum()
        check("Sum of title (1st-place) probabilities across all 20 teams is ~1", abs(title_col_sum - 1.0) < 0.02, f"sum={title_col_sum:.4f}")
        relegation_sum = pos_dist[["finish_18_probability", "finish_19_probability", "finish_20_probability"]].sum().sum()
        check("Sum of relegation-zone (18th-20th) probabilities across all 20 teams is ~3", abs(relegation_sum - 3.0) < 0.05, f"sum={relegation_sum:.4f}")

        table = pd.read_csv(expected_table_path)
        check("Expected table has exactly 20 teams, no duplicates", len(table) == 20 and table["team"].duplicated().sum() == 0)
        check(
            "Relegation/top-4/top-5/title probabilities are internally consistent (title<=top4<=top5<=top_half)",
            bool((table["title_probability"] <= table["top_4_probability"] + 1e-6).all()
                 and (table["top_4_probability"] <= table["top_5_probability"] + 1e-6).all()
                 and (table["top_5_probability"] <= table["top_half_probability"] + 1e-6).all()),
        )
        check(
            "Final table calculations are correct: expected_wins+draws+losses == 38 for every team",
            # Tolerance 0.02, not 0.01: wins/draws/losses are each independently
            # rounded to 2dp for display, so their sum can drift by up to
            # ~0.015 from 38 even when the underlying simulation is exact.
            bool(((table["expected_wins"] + table["expected_draws"] + table["expected_losses"]).sub(38).abs() < 0.02).all()),
        )

    not_applicable(
        "Weekly updates do not overwrite old prediction timestamps",
        "No weekly-update engine exists yet (2026-27 season has not started; today is preseason). Deferred to a later phase.",
    )
    not_applicable(
        "Simulation uses actual completed results locked + simulated future results",
        "No 2026-27 matches have been played yet (preseason_mode); all 380 fixtures are simulated as future matches, which is correct for this point in time, not a failure of the locking mechanism.",
    )
    not_applicable(
        "Closing odds are not leaked into pre-match predictions",
        "No odds feed (opening, current, or closing) is connected in Phase 1/2 at all -- there is nothing to leak. Will become a real check once a live odds feed is wired in.",
    )


def main() -> None:
    run_checks()
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_na = sum(1 for r in results if r["status"].startswith("N/A"))

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REPORT, "w") as f:
        f.write("# EPL 2026-27 Integrity Audit\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(f"**{n_pass} passed, {n_fail} failed, {n_na} not yet applicable** (out of {len(results)} checks).\n\n")
        f.write("| Status | Check | Detail |\n|---|---|---|\n")
        for r in results:
            f.write(f"| {r['status']} | {r['check']} | {r['detail']} |\n")
        f.write("\n## Reading N/A rows\n\n"
                "An \"N/A (feature not yet built)\" row is not a pass -- it means the corresponding pipeline "
                "stage (weekly updates, market integration) does not exist yet in this phase, so the check "
                "has nothing to verify. See reports/epl_2026_27_model_report.md \"Deferred to later phases\" "
                "for what's missing and why. These rows must become real PASS/FAIL checks, never be silently "
                "removed, once that functionality is built.\n")

    print(f"Integrity audit: {n_pass} passed, {n_fail} failed, {n_na} not yet applicable.")
    print(f"Report written to {OUT_REPORT}")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  FAIL: {r['check']} -- {r['detail']}")

    sys.exit(1 if n_fail > 0 else 0)


if __name__ == "__main__":
    main()
