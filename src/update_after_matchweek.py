"""Weekly-update engine (spec section 27).

Ingests real, caller-supplied completed-match results for a matchweek,
locks them in, refits team strength on historical + completed 2026-27
data, re-predicts the remaining (not-yet-played) fixtures, re-runs the
season simulation with real results-to-date as a fixed baseline, and
reports what changed versus the previous run.

**This cannot be exercised against real data yet**: today (2026-08-18)
is before kickoff (2026-08-21), so no real 2026-27 result exists. The
mechanism is built and tested against synthetic, clearly-labeled data
in `tests/test_completed_match_locking.py` and
`tests/test_weekly_update_versioning.py`, which point every write path
at a temporary directory via the `paths=` parameter below rather than
ever writing synthetic results into the real project data files -- so
it is ready to run for real the moment matchweek 1 finishes, without
having risked corrupting real data to prove it works.

The caller supplies a real results CSV with columns: match_id,
home_goals, away_goals, source_name, source_timestamp. Nothing here
invents a result -- if a match_id in the requested matchweek is not in
the results file, it is left as `scheduled` and simulated, not
silently marked complete.

Run: python -m src.update_after_matchweek --matchweek 1 --results path/to/results.csv
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.prediction_ledger import append_to_ledger, load_combined_match_odds  # noqa: E402
from src.evaluation.recalibration_gate import (  # noqa: E402
    EVALUATION_CADENCE_MATCHWEEKS as RECAL_CADENCE,
    MIN_MATCHES_TO_ATTEMPT as RECAL_MIN_MATCHES,
    N_BOOTSTRAP,
    attempt_recalibration,
)
from src.evaluation.score_weekly_results import append_season_probability_path, score_after_matchweek  # noqa: E402
from src.models.predict_all_matches import (  # noqa: E402
    PREDICTION_COLUMNS,
    build_model_context,
    predict_fixtures,
)
from src.simulation.simulate_full_season import run_monte_carlo  # noqa: E402
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

REQUIRED_RESULT_COLUMNS = ["match_id", "home_goals", "away_goals", "source_name", "source_timestamp"]

COMPLETED_MATCH_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "home_goals", "away_goals", "result",
    "home_xg", "away_xg", "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession", "home_ppda", "away_ppda", "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg", "home_red_cards", "away_red_cards", "referee", "stadium",
    "attendance", "source_name", "source_url_or_page_title", "source_timestamp", "is_real_data", "data_status", "notes",
]


@dataclass
class WeeklyUpdatePaths:
    """Every path this engine reads or writes, all overridable so tests
    can point the whole run at a temp directory instead of ever writing
    synthetic data into the real project files."""
    historical: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv")
    fixtures: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv")
    match_odds: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw" / "epl_2026_27_match_odds.csv")
    real_odds: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw" / "epl_2026_27_real_odds.csv")
    completed_2627: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw" / "epl_2026_27_completed_matches.csv")
    model_config: Path = field(default_factory=lambda: REPO_ROOT / "config" / "model_config.yaml")
    sim_config: Path = field(default_factory=lambda: REPO_ROOT / "config" / "simulation_config.yaml")
    predictions: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_match_predictions.csv")
    ledger: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_prediction_ledger.csv")
    expected_table: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_expected_table.csv")
    position_distribution: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_position_distribution.csv")
    weekly_dir: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "weekly")
    weekly_scoring: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_weekly_scoring.csv")
    reliability_running: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_reliability_running.csv")
    reliability_horizon: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_reliability_horizon.csv")
    season_probability_path: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_season_probability_path.csv")
    recalibration_decisions: Path = field(default_factory=lambda: REPO_ROOT / "data" / "outputs" / "epl_2026_27_recalibration_decisions.csv")
    active_calibrators: Path = field(default_factory=lambda: REPO_ROOT / "model_registry" / "active_calibrators.pkl")


DEFAULT_PATHS = WeeklyUpdatePaths()


def result_from_score(hg: int, ag: int) -> str:
    return "home_win" if hg > ag else ("away_win" if hg < ag else "draw")


def load_results(results_path: Path) -> pd.DataFrame:
    results = pd.read_csv(results_path)
    missing = set(REQUIRED_RESULT_COLUMNS) - set(results.columns)
    if missing:
        raise ValueError(f"results file is missing required columns: {missing}")
    return results


def lock_completed_matches(
    matchweek: int, results: pd.DataFrame, fixtures_df: pd.DataFrame, paths: WeeklyUpdatePaths,
) -> pd.DataFrame:
    """Merges real results into fixtures_df (status -> completed) and
    into the running completed-2026-27-matches file (same schema as
    epl_historical_matches.csv, so it can be concatenated directly for
    refitting). Returns the updated fixtures_df; writes the completed-
    matches file to disk. Never marks a match complete unless a real
    result for it was actually supplied."""
    mw_fixtures = fixtures_df[fixtures_df["matchweek"] == matchweek]
    unknown_ids = set(results["match_id"]) - set(fixtures_df["match_id"])
    if unknown_ids:
        raise ValueError(f"results file references match_id(s) not in the fixture list: {unknown_ids}")
    not_in_this_mw = set(results["match_id"]) - set(mw_fixtures["match_id"])
    if not_in_this_mw:
        raise ValueError(f"results file references match_id(s) not in matchweek {matchweek}: {not_in_this_mw}")

    if paths.completed_2627.exists():
        completed_df = pd.read_csv(paths.completed_2627)
    else:
        completed_df = pd.DataFrame(columns=COMPLETED_MATCH_COLUMNS)

    new_rows = []
    for _, r in results.iterrows():
        fx = fixtures_df[fixtures_df["match_id"] == r["match_id"]].iloc[0]
        hg, ag = int(r["home_goals"]), int(r["away_goals"])
        new_rows.append({
            "season": fx["season"], "match_id": fx["match_id"], "date": fx["date"],
            "home_team": fx["home_team"], "away_team": fx["away_team"],
            "home_goals": hg, "away_goals": ag, "result": result_from_score(hg, ag),
            "home_xg": "", "away_xg": "", "home_shots": "", "away_shots": "",
            "home_shots_on_target": "", "away_shots_on_target": "", "home_possession": "", "away_possession": "",
            "home_ppda": "", "away_ppda": "", "home_big_chances": "", "away_big_chances": "",
            "home_set_piece_xg": "", "away_set_piece_xg": "", "home_red_cards": "", "away_red_cards": "",
            "referee": "", "stadium": fx["stadium"], "attendance": "",
            "source_name": r["source_name"], "source_url_or_page_title": r.get("source_url_or_page_title", ""),
            "source_timestamp": r["source_timestamp"], "is_real_data": True, "data_status": "completed",
            "notes": r.get("notes", "Locked by src/update_after_matchweek.py"),
        })
    new_df = pd.DataFrame(new_rows)

    # Upsert: a re-submitted match_id (a correction) replaces its old row
    # rather than duplicating it.
    completed_df = completed_df[~completed_df["match_id"].isin(new_df["match_id"])]
    completed_df = pd.concat([completed_df, new_df], ignore_index=True)
    paths.completed_2627.parent.mkdir(parents=True, exist_ok=True)
    completed_df.to_csv(paths.completed_2627, index=False)

    fixtures_df = fixtures_df.copy()
    fixtures_df.loc[fixtures_df["match_id"].isin(new_df["match_id"]), "status"] = "completed"
    fixtures_df.to_csv(paths.fixtures, index=False)

    return fixtures_df


def team_locked_baseline(completed_df: pd.DataFrame, teams: list[str]) -> dict[str, dict]:
    """Real, already-happened points/GF/GA/W/D/L per team from locked
    2026-27 results only (not historical seasons)."""
    baseline = {t: {"points": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0} for t in teams}
    for _, m in completed_df.iterrows():
        h, a, hg, ag = m["home_team"], m["away_team"], int(m["home_goals"]), int(m["away_goals"])
        if h not in baseline or a not in baseline:
            continue
        baseline[h]["gf"] += hg
        baseline[h]["ga"] += ag
        baseline[a]["gf"] += ag
        baseline[a]["ga"] += hg
        if hg > ag:
            baseline[h]["points"] += 3
            baseline[h]["w"] += 1
            baseline[a]["l"] += 1
        elif hg < ag:
            baseline[a]["points"] += 3
            baseline[a]["w"] += 1
            baseline[h]["l"] += 1
        else:
            baseline[h]["points"] += 1
            baseline[a]["points"] += 1
            baseline[h]["d"] += 1
            baseline[a]["d"] += 1
    return baseline


def run_update(matchweek: int, results_path: Path, paths: WeeklyUpdatePaths = DEFAULT_PATHS) -> dict:
    """Returns a dict of the key in-memory results (fixtures_df,
    final_predictions, new_expected_table, new_position_dist,
    probability_changes) so tests can assert on them directly rather
    than re-reading files."""
    with open(paths.model_config) as f:
        model_cfg = yaml.safe_load(f)
    with open(paths.sim_config) as f:
        sim_cfg = yaml.safe_load(f)

    results = load_results(results_path)
    fixtures_df = pd.read_csv(paths.fixtures)
    fixtures_df = lock_completed_matches(matchweek, results, fixtures_df, paths)
    print(f"Locked {len(results)} real result(s) for matchweek {matchweek}.")

    historical_df = pd.read_csv(paths.historical, parse_dates=["date"])
    historical_clean = historical_df.dropna(subset=["home_goals", "away_goals"])
    completed_2627 = pd.read_csv(paths.completed_2627, parse_dates=["date"])
    df_for_fit = pd.concat([historical_clean, completed_2627], ignore_index=True)

    hist_teams = sorted(set(df_for_fit["home_team"]) | set(df_for_fit["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))
    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    ctx = build_model_context(df_for_fit, universe, model_cfg, as_of_date, active_calibrators_path=paths.active_calibrators)

    remaining_fixtures = fixtures_df[fixtures_df["status"] != "completed"].copy()
    generated_at = now_utc_iso()
    meta = make_run_metadata(
        prefix="weekly_update", season="2026-27",
        calibration_method=ctx["calibration_method"], latest_source_timestamp_used=str(results["source_timestamp"].max()),
    )
    pred_rows, expl_rows = predict_fixtures(remaining_fixtures, ctx, df_for_fit, model_cfg, "early_week_mode", generated_at, meta.run_id)
    weekly_predictions = pd.DataFrame(pred_rows)[PREDICTION_COLUMNS] if pred_rows else pd.DataFrame(columns=PREDICTION_COLUMNS)

    append_to_ledger(pred_rows, paths.ledger, match_odds_by_id=load_combined_match_odds(paths.real_odds, paths.match_odds))

    # Merge into the main predictions file: completed matches keep their
    # ORIGINAL pre-match prediction (never overwritten) with the real
    # result appended; remaining matches get the freshly refit prediction.
    if paths.predictions.exists():
        existing = pd.read_csv(paths.predictions)
    else:
        existing = pd.DataFrame(columns=PREDICTION_COLUMNS)
    completed_ids = set(fixtures_df.loc[fixtures_df["status"] == "completed", "match_id"])
    results_by_id = completed_2627.set_index("match_id")

    updated_existing = existing.copy()
    for match_id in completed_ids:
        if match_id not in results_by_id.index or match_id not in updated_existing.get("match_id", pd.Series(dtype=str)).values:
            continue
        row = results_by_id.loc[match_id]
        idx = updated_existing.index[updated_existing["match_id"] == match_id][0]
        updated_existing.loc[idx, "status"] = "completed"
        updated_existing.loc[idx, "actual_home_goals"] = row["home_goals"]
        updated_existing.loc[idx, "actual_away_goals"] = row["away_goals"]
        updated_existing.loc[idx, "actual_result"] = row["result"]

    kept_existing = updated_existing[updated_existing["match_id"].isin(completed_ids)] if not updated_existing.empty else updated_existing
    final_predictions = pd.concat([kept_existing, weekly_predictions], ignore_index=True)
    final_predictions = final_predictions.sort_values(["matchweek", "kickoff_utc"]).reset_index(drop=True)
    paths.predictions.parent.mkdir(parents=True, exist_ok=True)
    final_predictions.to_csv(paths.predictions, index=False)

    teams_2627 = EPL_2026_27_CLUBS
    baseline = team_locked_baseline(completed_2627, teams_2627)
    initial_points = {t: baseline[t]["points"] for t in teams_2627}
    initial_gf = {t: baseline[t]["gf"] for t in teams_2627}
    initial_ga = {t: baseline[t]["ga"] for t in teams_2627}
    initial_wins = {t: baseline[t]["w"] for t in teams_2627}
    initial_draws = {t: baseline[t]["d"] for t in teams_2627}
    initial_losses = {t: baseline[t]["l"] for t in teams_2627}

    old_expected_table = pd.read_csv(paths.expected_table) if paths.expected_table.exists() else None

    new_expected_table, new_position_dist = run_monte_carlo(
        remaining_fixtures, ctx["fit"], teams_2627, sim_cfg["n_simulations"], sim_cfg["random_seed"], sim_cfg,
        ctx["promoted_rating_dist"],
        initial_points=initial_points, initial_goals_for=initial_gf, initial_goals_against=initial_ga,
        initial_wins=initial_wins, initial_draws=initial_draws, initial_losses=initial_losses,
    )
    new_expected_table.to_csv(paths.expected_table, index=False)
    new_position_dist.to_csv(paths.position_distribution, index=False)
    append_season_probability_path(matchweek, new_expected_table, paths)

    paths.weekly_dir.mkdir(parents=True, exist_ok=True)
    weekly_predictions.to_csv(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_predictions.csv", index=False)
    new_expected_table.to_csv(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_expected_table.csv", index=False)
    new_position_dist.to_csv(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_position_distribution.csv", index=False)

    probability_changes = pd.DataFrame()
    if old_expected_table is not None:
        merged = old_expected_table[["team", "title_probability", "top_4_probability", "relegation_probability", "expected_points"]].merge(
            new_expected_table[["team", "title_probability", "top_4_probability", "relegation_probability", "expected_points"]],
            on="team", suffixes=("_before", "_after"),
        )
        merged["title_probability_change"] = merged["title_probability_after"] - merged["title_probability_before"]
        merged["top_4_probability_change"] = merged["top_4_probability_after"] - merged["top_4_probability_before"]
        merged["relegation_probability_change"] = merged["relegation_probability_after"] - merged["relegation_probability_before"]
        merged["expected_points_change"] = merged["expected_points_after"] - merged["expected_points_before"]
        probability_changes = merged.sort_values("title_probability_change", ascending=False)
        probability_changes.to_csv(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_probability_changes.csv", index=False)

    # Score the just-locked matchweek's real results against the
    # pre-kickoff predictions actually made for them (leak-checked via
    # the ledger -- see prediction_ledger.select_pre_kickoff_predictions).
    scoring = score_after_matchweek(matchweek, paths)

    # Gated challenger recalibration -- a documented no-op below 60 real
    # matches, never silently swaps the production calibrator (see
    # recalibration_gate.py docstring).
    recalibration = attempt_recalibration(paths, matchweek=matchweek)

    with open(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_update_report.md", "w") as f:
        f.write(f"# EPL Matchweek {matchweek} Update Report\n\n")
        f.write(f"Generated: {generated_at}\n\n")
        f.write(f"Locked {len(results)} real result(s). {len(remaining_fixtures)} fixtures remain to be predicted/simulated.\n\n")
        if not probability_changes.empty:
            f.write("## Biggest title-probability movers\n\n")
            f.write(probability_changes[["team", "title_probability_change", "top_4_probability_change", "relegation_probability_change"]].head(10).to_markdown(index=False))
            f.write("\n\n")

        f.write("## Scoring\n\n"
                "Two tracks, never pooled: **preseason** is the frozen `preseason-2026-27-v2` tag's "
                "forecast (no dc_raw baseline available for it -- that field didn't exist yet when v2 "
                "was tagged); **operational** is the model's latest pre-kickoff prediction at any point "
                "in the season.\n\n")
        f.write(f"This matchweek ({len(scoring['gameweek_scored'])} scored match(es)):\n\n")
        f.write(scoring["gameweek_metrics"][["track", "model", "n_matches", "log_loss", "brier", "rps"]].to_markdown(index=False))
        f.write(f"\n\nCumulative, all {len(scoring['cumulative_scored'])} real match(es) scored so far this season:\n\n")
        f.write(scoring["cumulative_metrics"][["track", "model", "n_matches", "log_loss", "brier", "rps"]].to_markdown(index=False))
        f.write("\n\n'production' is what the pipeline actually predicted (calibrated Dixon-Coles, "
                "or the ensemble on the seasons it's statistically justified, or a promoted challenger); "
                "'dc_raw' is the uncalibrated Dixon-Coles baseline; 'market' is 0 matches until a real "
                "match-odds snapshot is logged for that fixture (see 'Data-quality warnings' below).\n\n")

        if not scoring["surprising_results"].empty:
            f.write("## Most surprising results\n\n"
                    "Matches where the actual outcome sat furthest into the model's predicted tail "
                    "(lowest probability assigned to what actually happened):\n\n")
            f.write(scoring["surprising_results"][[
                "home_team", "away_team", "actual_result", "predicted_probability_of_actual_outcome",
            ]].to_markdown(index=False))
            f.write("\n\n")

        if recalibration is not None:
            f.write("## Recalibration gate\n\n")
            f.write(
                f"Attempted (>= {RECAL_MIN_MATCHES} real matches, matchweek is a multiple of "
                f"{RECAL_CADENCE}): **{recalibration['decision']}**. Rolling-origin paired bootstrap "
                f"({recalibration['n_paired_observations']} paired observations, {N_BOOTSTRAP} resamples): "
                f"log-loss difference (incumbent - challenger) point estimate "
                f"{recalibration['point_estimate_log_loss_diff']:.4f}, 95% CI "
                f"[{recalibration['ci_low']:.4f}, {recalibration['ci_high']:.4f}]. Challenger method: "
                f"{recalibration['challenger_method']}. Promotion requires the full CI on the "
                f"challenger-is-better side. See `{paths.recalibration_decisions.name}` for the full decision log.\n\n"
            )
        else:
            f.write("## Recalibration gate\n\n"
                    f"Not attempted this matchweek -- either fewer than {RECAL_MIN_MATCHES} real completed "
                    "matches exist yet, or this matchweek is not on the evaluation cadence "
                    f"(every {RECAL_CADENCE}th matchweek, recalibration_gate.py's "
                    "EVALUATION_CADENCE_MATCHWEEKS, to avoid repeated-testing across the season). No "
                    "automatic weekly recalibration ever runs; this gate only activates on cadence, and "
                    "only promotes a challenger backed by a paired-bootstrap 95% CI on rolling-origin "
                    "evaluations across the whole season so far.\n\n")

        f.write("## Data-quality warnings\n\n"
                "- Injury, lineup, and market-odds data remain unavailable (see config/data_sources.yaml) -- "
                "this update only incorporates real completed-match results and team-strength re-fitting.\n")

    log_experiment(meta, stage="weekly_update", notes=f"matchweek={matchweek}, {len(results)} results locked, {len(remaining_fixtures)} fixtures remaining")
    print(f"Wrote weekly update outputs for matchweek {matchweek} to {paths.weekly_dir}")

    return {
        "fixtures_df": fixtures_df,
        "final_predictions": final_predictions,
        "new_expected_table": new_expected_table,
        "new_position_dist": new_position_dist,
        "probability_changes": probability_changes,
        "scoring": scoring,
        "recalibration": recalibration,
        "run_id": meta.run_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lock a matchweek's real results and re-predict the rest of the season.")
    parser.add_argument("--matchweek", type=int, required=True)
    parser.add_argument("--results", type=Path, required=True, help="CSV with match_id,home_goals,away_goals,source_name,source_timestamp")
    args = parser.parse_args()
    run_update(args.matchweek, args.results)


if __name__ == "__main__":
    main()
