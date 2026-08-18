"""Scores real, completed 2026-27 matchweeks against the pre-kickoff
predictions that were actually made for them -- the missing "(c)" from
the weekly-update audit: `update_after_matchweek.py` refits and
re-predicts every week, but nothing was checking how good those
predictions actually were once results landed.

Every prediction scored here comes from `prediction_ledger.select_pre_
kickoff_predictions`, which only ever returns a row whose `generated_at`
predates the match's own `kickoff_utc` -- this is the leak-check made
operational (an assertion, not a design intention). A match with no
qualifying pre-kickoff row raises rather than silently scoring nothing
or falling back to a regenerated, potentially-leaked prediction.

Deliberately does NOT recalibrate anything based on these scores --
see `recalibration_gate.py` for why (10 matches/gameweek is far too
small a sample to adjust on) and how the gated, held-out-validated
challenger process works once enough real data exists.

Run: python -m src.evaluation.score_weekly_results --matchweek 1
(reads/writes via the real DEFAULT_PATHS; pass a WeeklyUpdatePaths for
tests, exactly like update_after_matchweek.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import RESULT_ORDER, brier_row, log_loss_row, rps  # noqa: E402
from src.evaluation.prediction_ledger import read_ledger, select_pre_kickoff_predictions  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

N_RELIABILITY_BINS = 10
N_SURPRISING_RESULTS = 10

PROB_COLUMN_SETS = {
    "production": ("home_win_prob", "draw_prob", "away_win_prob"),
    "dc_raw": ("dc_raw_home_win_prob", "dc_raw_draw_prob", "dc_raw_away_win_prob"),
    "market": ("market_home_win_prob", "market_draw_prob", "market_away_win_prob"),
}


def _probs_from_row(row: pd.Series, model: str) -> dict | None:
    h_col, d_col, a_col = PROB_COLUMN_SETS[model]
    if model == "market" and not bool(row.get("market_available", False)):
        return None
    h, d, a = row.get(h_col), row.get(d_col), row.get(a_col)
    if pd.isna(h) or pd.isna(d) or pd.isna(a):
        return None
    return {"home_win": float(h), "draw": float(d), "away_win": float(a)}


def score_predictions(scored: pd.DataFrame) -> pd.DataFrame:
    """`scored` must have one row per match with pre-kickoff prediction
    columns (from the ledger) plus `actual_result`. Returns long-format
    per-model, per-metric aggregate rows."""
    rows = []
    for model in PROB_COLUMN_SETS:
        log_losses, briers, rpss = [], [], []
        for _, r in scored.iterrows():
            probs = _probs_from_row(r, model)
            if probs is None:
                continue
            actual = r["actual_result"]
            log_losses.append(log_loss_row(probs, actual))
            briers.append(brier_row(probs, actual))
            rpss.append(rps(probs, actual))
        n = len(log_losses)
        rows.append({
            "model": model, "n_matches": n,
            "log_loss": round(float(np.mean(log_losses)), 4) if n else None,
            "brier": round(float(np.mean(briers)), 4) if n else None,
            "rps": round(float(np.mean(rpss)), 4) if n else None,
        })
    return pd.DataFrame(rows)


def build_reliability_table(scored: pd.DataFrame, model: str = "production") -> pd.DataFrame:
    """Same binning convention as calibrate_probabilities._reliability_table,
    but over real 2026-27 results scored so far rather than the static
    historical backtest."""
    h_col, d_col, a_col = PROB_COLUMN_SETS[model]
    rows = []
    bins = np.linspace(0, 1, N_RELIABILITY_BINS + 1)
    for cls, col in [("home_win", h_col), ("draw", d_col), ("away_win", a_col)]:
        raw = scored[col].astype(float)
        target = (scored["actual_result"] == cls).astype(int)
        bin_idx = np.clip(np.digitize(raw, bins) - 1, 0, N_RELIABILITY_BINS - 1)
        for b in range(N_RELIABILITY_BINS):
            mask = bin_idx == b
            n = int(mask.sum())
            rows.append({
                "outcome_class": cls, "bin_lower": round(bins[b], 2), "bin_upper": round(bins[b + 1], 2),
                "n_matches": n,
                "mean_predicted_probability": round(float(raw[mask].mean()), 4) if n else "",
                "empirical_frequency": round(float(target[mask].mean()), 4) if n else "",
            })
    return pd.DataFrame(rows)


def most_surprising_results(scored: pd.DataFrame, n: int = N_SURPRISING_RESULTS) -> pd.DataFrame:
    """Ranks matches by how much probability mass the production model
    assigned to what actually happened -- lowest first (most surprising:
    the model thought this outcome was the least likely of the three)."""
    rows = []
    for _, r in scored.iterrows():
        probs = _probs_from_row(r, "production")
        if probs is None:
            continue
        actual = r["actual_result"]
        rows.append({
            "match_id": r["match_id"], "matchweek": r["matchweek"],
            "home_team": r["home_team"], "away_team": r["away_team"],
            "actual_result": actual,
            "predicted_probability_of_actual_outcome": round(probs[actual], 4),
            "home_win_prob": probs["home_win"], "draw_prob": probs["draw"], "away_win_prob": probs["away_win"],
            "surprise_log_loss": round(log_loss_row(probs, actual), 4),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("predicted_probability_of_actual_outcome", ascending=True).head(n).reset_index(drop=True)


def score_after_matchweek(matchweek: int, paths) -> dict:
    """Entry point called automatically by `update_after_matchweek.run_
    update()` right after a matchweek's results are locked. Scores (a)
    just this matchweek's matches and (b) every real match completed so
    far this season (cumulative), against production/dc_raw/market
    baselines, plus a running reliability table and a most-surprising-
    results list for this matchweek. Returns everything in-memory too so
    tests can assert on it without re-reading files."""
    ledger = read_ledger(paths.ledger)
    completed = pd.read_csv(paths.completed_2627, parse_dates=["date"])
    if completed.empty:
        raise ValueError("no completed 2026-27 matches to score yet")

    completed_ids = completed["match_id"].tolist()
    fixtures_df = pd.read_csv(paths.fixtures)
    mw_ids = fixtures_df.loc[fixtures_df["matchweek"] == matchweek, "match_id"]
    mw_ids = [m for m in mw_ids if m in set(completed_ids)]

    def _scored_frame(match_ids: list) -> pd.DataFrame:
        selected = select_pre_kickoff_predictions(ledger, match_ids=match_ids)
        return selected.merge(completed[["match_id", "result"]].rename(columns={"result": "actual_result"}), on="match_id")

    gameweek_scored = _scored_frame(mw_ids)
    cumulative_scored = _scored_frame(completed_ids)

    gameweek_metrics = score_predictions(gameweek_scored)
    gameweek_metrics.insert(0, "scope", f"matchweek_{matchweek}")
    cumulative_metrics = score_predictions(cumulative_scored)
    cumulative_metrics.insert(0, "scope", "cumulative")

    generated_at = now_utc_iso()
    weekly_scoring = pd.concat([gameweek_metrics, cumulative_metrics], ignore_index=True)
    weekly_scoring.insert(0, "matchweek", matchweek)
    weekly_scoring["generated_at"] = generated_at

    reliability = build_reliability_table(cumulative_scored, model="production")
    reliability.insert(0, "matchweek", matchweek)
    reliability["generated_at"] = generated_at

    surprising = most_surprising_results(gameweek_scored)
    if not surprising.empty:
        surprising["generated_at"] = generated_at

    # Append-only: weekly_scoring accumulates one block per matchweek call.
    paths.weekly_scoring.parent.mkdir(parents=True, exist_ok=True)
    write_header = not paths.weekly_scoring.exists()
    weekly_scoring.to_csv(paths.weekly_scoring, mode="a", header=write_header, index=False)

    # Reliability is a recomputed-to-date snapshot (like the static
    # historical version), not an append-only ledger -- overwritten with
    # the latest cumulative state each time.
    reliability.to_csv(paths.reliability_running, index=False)

    if not surprising.empty:
        paths.weekly_dir.mkdir(parents=True, exist_ok=True)
        surprising.to_csv(paths.weekly_dir / f"epl_matchweek_{matchweek:02d}_surprising_results.csv", index=False)

    return {
        "gameweek_metrics": gameweek_metrics,
        "cumulative_metrics": cumulative_metrics,
        "reliability": reliability,
        "surprising_results": surprising,
        "gameweek_scored": gameweek_scored,
        "cumulative_scored": cumulative_scored,
    }


def append_season_probability_path(matchweek: int, expected_table: pd.DataFrame, paths) -> None:
    """Append-only record of the title/top-4/relegation probability path
    over the season: one 20-row block per matchweek, so the FULL
    trajectory of these probabilities can be reconstructed and plotted
    later, not just the current snapshot."""
    block = expected_table[["team", "title_probability", "top_4_probability", "relegation_probability", "expected_points"]].copy()
    block.insert(0, "matchweek", matchweek)
    block["generated_at"] = now_utc_iso()
    paths.season_probability_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not paths.season_probability_path.exists()
    block.to_csv(paths.season_probability_path, mode="a", header=write_header, index=False)


def main() -> None:
    import argparse

    from src.update_after_matchweek import DEFAULT_PATHS

    parser = argparse.ArgumentParser(description="Score a completed matchweek's predictions against real results.")
    parser.add_argument("--matchweek", type=int, required=True)
    args = parser.parse_args()
    result = score_after_matchweek(args.matchweek, DEFAULT_PATHS)
    print(result["gameweek_metrics"].to_string(index=False))
    print()
    print(result["cumulative_metrics"].to_string(index=False))


if __name__ == "__main__":
    main()
