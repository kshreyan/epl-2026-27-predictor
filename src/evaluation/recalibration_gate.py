"""Gated challenger recalibration -- explicitly NOT an automatic weekly
recalibration loop.

Ten matches a gameweek is far too small a sample to safely recalibrate
on; doing so would fit noise, not signal. This module only activates
once `MIN_MATCHES_TO_ATTEMPT` (60) real, completed 2026-27 matches
exist -- below that, `attempt_recalibration` is a documented no-op.
Even once active, it never silently swaps anything in: it fits a
CHALLENGER calibrator (static historical backtest + all real 2026-27
results EXCEPT a held-out slice of the most recent real matches),
evaluates both the challenger and the current INCUMBENT calibrator
(the static historical-only fit already used in production) on that
held-out slice -- which neither has seen -- and only writes the
challenger as the new active calibrator if it strictly beats the
incumbent's log loss there. Every attempt, promoted or not, is logged
with its exact numbers to an append-only decision log.

Run: python -m src.evaluation.recalibration_gate
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.calibration.calibrate_probabilities import CLASSES, apply_calibration, fit_calibrators  # noqa: E402
from src.evaluation.backtest import log_loss_row  # noqa: E402
from src.evaluation.prediction_ledger import read_ledger, select_pre_kickoff_predictions  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"

MIN_MATCHES_TO_ATTEMPT = 60
N_HOLDOUT = 20  # roughly 2 gameweeks -- the most recent real matches, held out from BOTH calibrators' fits

RECALIBRATION_DECISION_COLUMNS = [
    "decision_id", "generated_at", "n_real_matches_total", "n_real_matches_train", "n_holdout",
    "incumbent_log_loss_holdout", "challenger_log_loss_holdout", "decision", "notes",
]


def _real_scored_df(paths) -> pd.DataFrame:
    """Every real, completed 2026-27 match with its PROVABLY pre-kickoff
    raw Dixon-Coles probabilities (via the ledger's leak-check) and
    actual result, ordered chronologically by kickoff."""
    ledger = read_ledger(paths.ledger)
    completed = pd.read_csv(paths.completed_2627, parse_dates=["date"])
    if completed.empty:
        return pd.DataFrame()
    selected = select_pre_kickoff_predictions(ledger, match_ids=completed["match_id"].tolist())
    scored = selected.merge(completed[["match_id", "result"]].rename(columns={"result": "actual_result"}), on="match_id")
    return scored.sort_values("kickoff_utc").reset_index(drop=True)


def _to_backtest_schema(scored: pd.DataFrame) -> pd.DataFrame:
    """Renames the ledger's dc_raw_* columns to the static backtest
    file's dc_home_win/dc_draw/dc_away_win schema so the two can be
    concatenated and fed to the existing fit_calibrators()."""
    return pd.DataFrame({
        "dc_home_win": scored["dc_raw_home_win_prob"], "dc_draw": scored["dc_raw_draw_prob"],
        "dc_away_win": scored["dc_raw_away_win_prob"], "actual_result": scored["actual_result"],
    })


def _evaluate(calibrators: dict, holdout: pd.DataFrame) -> float:
    losses = []
    for _, r in holdout.iterrows():
        raw = {"home_win": r["dc_home_win"], "draw": r["dc_draw"], "away_win": r["dc_away_win"]}
        calibrated = apply_calibration(calibrators, raw)
        losses.append(log_loss_row(calibrated, r["actual_result"]))
    return float(pd.Series(losses).mean())


def attempt_recalibration(paths, backtest_path: Path | None = None) -> dict | None:
    """Returns None (a documented no-op) below MIN_MATCHES_TO_ATTEMPT.
    Otherwise fits and evaluates a challenger, logs the decision, and --
    only if the challenger wins -- writes it as the new active
    calibrator. Returns the full decision dict either way (None only
    when the gate didn't even attempt). `backtest_path` is overridable
    so tests never need to read or write the real static backtest file."""
    real_scored = _real_scored_df(paths)
    n_real = len(real_scored)
    if n_real < MIN_MATCHES_TO_ATTEMPT:
        return None

    backtest_path = backtest_path if backtest_path is not None else BACKTEST_PATH
    if not backtest_path.exists():
        return None

    backtest_df = pd.read_csv(backtest_path)
    real_backtest_shaped = _to_backtest_schema(real_scored)

    n_holdout = min(N_HOLDOUT, n_real // 3)  # never hold out more than a third of what's available
    real_train = real_backtest_shaped.iloc[: n_real - n_holdout]
    real_holdout = real_backtest_shaped.iloc[n_real - n_holdout:]

    incumbent = fit_calibrators(backtest_df)
    challenger_fit_df = pd.concat([backtest_df[["dc_home_win", "dc_draw", "dc_away_win", "actual_result"]], real_train], ignore_index=True)
    challenger = fit_calibrators(challenger_fit_df)

    incumbent_loss = _evaluate(incumbent, real_holdout)
    challenger_loss = _evaluate(challenger, real_holdout)
    decision = "PROMOTED" if challenger_loss < incumbent_loss else "REJECTED"

    generated_at = now_utc_iso()
    decision_id = f"recal_{generated_at.replace(':', '').replace('-', '')}"
    decision_row = pd.DataFrame([{
        "decision_id": decision_id, "generated_at": generated_at,
        "n_real_matches_total": n_real, "n_real_matches_train": len(real_train), "n_holdout": len(real_holdout),
        "incumbent_log_loss_holdout": round(incumbent_loss, 4), "challenger_log_loss_holdout": round(challenger_loss, 4),
        "decision": decision,
        "notes": (
            f"challenger = static historical backtest ({len(backtest_df)} matches) + first "
            f"{len(real_train)} real 2026-27 matches; evaluated on the {len(real_holdout)} most "
            "recent real matches, held out from both fits."
        ),
    }])
    paths.recalibration_decisions.parent.mkdir(parents=True, exist_ok=True)
    write_header = not paths.recalibration_decisions.exists()
    decision_row.to_csv(paths.recalibration_decisions, mode="a", header=write_header, index=False)

    if decision == "PROMOTED":
        paths.active_calibrators.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.active_calibrators, "wb") as f:
            pickle.dump({"calibrators": challenger, "decision_id": decision_id, "generated_at": generated_at}, f)

    return {
        "decision": decision, "decision_id": decision_id,
        "incumbent_log_loss_holdout": incumbent_loss, "challenger_log_loss_holdout": challenger_loss,
        "n_real_matches_total": n_real, "n_train": len(real_train), "n_holdout": len(real_holdout),
        "challenger_calibrators": challenger,
    }


def load_active_calibrators(active_calibrators_path: Path) -> dict | None:
    """Used by predict_all_matches.build_model_context: if a challenger
    has ever been promoted, its calibrators are used in place of the
    static historical-only fit -- until a LATER challenger beats it in
    turn (this file is simply overwritten by the next promotion, but
    every promotion is still permanently recorded in the append-only
    decision log regardless of what the active file currently holds)."""
    if not active_calibrators_path.exists():
        return None
    with open(active_calibrators_path, "rb") as f:
        payload = pickle.load(f)
    return payload["calibrators"]


def main() -> None:
    from src.update_after_matchweek import DEFAULT_PATHS

    result = attempt_recalibration(DEFAULT_PATHS)
    if result is None:
        print(f"No-op: fewer than {MIN_MATCHES_TO_ATTEMPT} real completed 2026-27 matches exist yet.")
        return
    print(f"Decision: {result['decision']} (incumbent log loss {result['incumbent_log_loss_holdout']:.4f} "
          f"vs challenger {result['challenger_log_loss_holdout']:.4f} on {result['n_holdout']} held-out matches)")


if __name__ == "__main__":
    main()
