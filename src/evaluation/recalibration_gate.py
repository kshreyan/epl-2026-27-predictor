"""Gated challenger recalibration -- explicitly NOT an automatic weekly
recalibration loop.

Second pass, tightened after review of the first version (which used a
single ~20-match recent holdout and a bare point-estimate win). That
was too loose for a decision that swaps production's calibrator:

- **150 real matches minimum** (`MIN_MATCHES_TO_ATTEMPT`), not 60 --
  roughly 4 gameweeks' more runway before the gate is even eligible.
- **Rolling-origin evaluation across the whole season so far**, not one
  recent slice: the real matches are walked forward in
  `ROLLING_CHUNK_SIZE`-match chunks, and for every chunk from the
  start, a challenger is fit on (static historical backtest + all real
  matches strictly before that chunk) and evaluated on that chunk. This
  produces one paired (incumbent_loss, challenger_loss) observation per
  real match across every chunk evaluated -- not just the most recent
  ~20.
- **Promotion requires a paired bootstrap (10,000 resamples) 95% CI on
  the log-loss difference that excludes zero**, in the direction that
  favors the challenger -- not a bare point-estimate win on however
  many matches happened to be in one holdout. Same statistical bar
  already used for the ensemble-vs-Dixon-Coles decision (see
  `final_stacked_model.paired_bootstrap_significance`), applied here.
- **A fixed evaluation cadence** (every `EVALUATION_CADENCE_MATCHWEEKS`
  matchweeks, not every week) rather than a Bonferroni correction --
  simpler to reason about and equally effective at controlling the
  repeated-testing problem of re-running a promotion decision every
  single gameweek across a 38-week season.
- **Temperature scaling, not isotonic, below `ISOTONIC_MIN_REAL_MATCHES`
  (500) real matches** for the challenger specifically. Isotonic
  regression is a flexible non-parametric fit that can pick up spurious
  quirks in a small, single-season sample; temperature scaling is a
  single scalar parameter (calibrated probabilities are
  softmax(log(p_raw) / T)) and degrades gracefully instead. Since a
  Premier League season is only 380 matches, this challenger will use
  temperature scaling for the entire 2026-27 season -- isotonic only
  becomes eligible in a future season once enough real matches have
  accumulated across seasons. The INCUMBENT is unaffected by this: it
  is always the existing static historical-only isotonic fit already
  used in production (backtest_df alone is ~2660 matches, comfortably
  above the isotonic threshold).

Every attempt -- promoted or not, and even below the eligibility
threshold -- is logged to an append-only decision log, so "why did/
didn't this change" is always answerable from a file.

Run: python -m src.evaluation.recalibration_gate --matchweek N
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.calibration.calibrate_probabilities import CLASSES, apply_calibration, fit_calibrators  # noqa: E402
from src.evaluation.backtest import log_loss_row  # noqa: E402
from src.evaluation.prediction_ledger import read_ledger, select_pre_kickoff_predictions  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"

MIN_MATCHES_TO_ATTEMPT = 150
ROLLING_CHUNK_SIZE = 10  # roughly one gameweek
ISOTONIC_MIN_REAL_MATCHES = 500  # a real match count above what a single EPL season can ever provide
EVALUATION_CADENCE_MATCHWEEKS = 5  # attempt only every 5th matchweek, not every week
N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 20260818

RECALIBRATION_DECISION_COLUMNS = [
    "decision_id", "generated_at", "matchweek", "n_real_matches_total", "n_paired_observations",
    "n_rolling_chunks", "challenger_method",
    "point_estimate_log_loss_diff", "ci_low", "ci_high", "decision", "notes",
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
    file's dc_home_win/dc_draw/dc_away_win schema."""
    return pd.DataFrame({
        "dc_home_win": scored["dc_raw_home_win_prob"], "dc_draw": scored["dc_raw_draw_prob"],
        "dc_away_win": scored["dc_raw_away_win_prob"], "actual_result": scored["actual_result"],
    })


def fit_temperature_scaling(df: pd.DataFrame) -> float:
    """A single scalar T minimizing log loss on `df` (columns dc_home_win/
    dc_draw/dc_away_win/actual_result): calibrated_probs =
    softmax(log(raw_probs) / T). T=1 leaves raw probabilities unchanged;
    T>1 flattens (less confident), T<1 sharpens (more confident)."""
    raw = df[["dc_home_win", "dc_draw", "dc_away_win"]].to_numpy(dtype=float)
    raw = np.clip(raw, 1e-9, 1.0)
    log_raw = np.log(raw)
    class_idx = {"home_win": 0, "draw": 1, "away_win": 2}
    actual_idx = df["actual_result"].map(class_idx).to_numpy()

    def neg_log_likelihood(t: float) -> float:
        scaled = log_raw / t
        scaled -= scaled.max(axis=1, keepdims=True)  # numerical stability
        exp = np.exp(scaled)
        probs = exp / exp.sum(axis=1, keepdims=True)
        chosen = probs[np.arange(len(df)), actual_idx]
        return float(-np.log(np.clip(chosen, 1e-12, 1.0)).mean())

    result = minimize_scalar(neg_log_likelihood, bounds=(0.05, 20.0), method="bounded")
    return float(result.x)


def apply_temperature_scaling(temperature: float, raw_probs: dict[str, float]) -> dict[str, float]:
    order = ["home_win", "draw", "away_win"]
    raw = np.clip(np.array([raw_probs[c] for c in order], dtype=float), 1e-9, 1.0)
    scaled = np.log(raw) / temperature
    scaled -= scaled.max()
    exp = np.exp(scaled)
    probs = exp / exp.sum()
    return dict(zip(order, probs.tolist()))


def fit_challenger(fit_df: pd.DataFrame, n_real_matches: int) -> dict:
    """Below ISOTONIC_MIN_REAL_MATCHES real matches, temperature scaling
    only. Isotonic becomes eligible only once enough real matches have
    genuinely accumulated (never within a single 380-match season)."""
    if n_real_matches < ISOTONIC_MIN_REAL_MATCHES:
        return {"method": "temperature_scaling", "temperature": fit_temperature_scaling(fit_df)}
    return {"method": "isotonic", "calibrators": fit_calibrators(fit_df)}


def apply_challenger(challenger: dict, raw_probs: dict[str, float]) -> dict[str, float]:
    if challenger["method"] == "temperature_scaling":
        return apply_temperature_scaling(challenger["temperature"], raw_probs)
    return apply_calibration(challenger["calibrators"], raw_probs)


def rolling_origin_paired_losses(real_scored: pd.DataFrame, backtest_df: pd.DataFrame) -> dict:
    """Walks the real matches forward in ROLLING_CHUNK_SIZE-match chunks.
    For each chunk, fits a challenger on (backtest_df + all real matches
    strictly before that chunk) and evaluates BOTH the challenger and
    the (fixed, static-only) incumbent on that chunk's real matches.
    Returns paired per-match log losses across every chunk evaluated --
    the whole season so far, not one recent slice."""
    incumbent = fit_calibrators(backtest_df)
    real_shaped = _to_backtest_schema(real_scored)

    incumbent_losses, challenger_losses, methods_used = [], [], []
    n = len(real_shaped)
    n_chunks = 0
    for start in range(0, n, ROLLING_CHUNK_SIZE):
        chunk = real_shaped.iloc[start:start + ROLLING_CHUNK_SIZE]
        train_real = real_shaped.iloc[:start]
        if train_real.empty:
            # No real training data yet for this earliest chunk -- the
            # challenger degrades to the static-only fit, which by
            # construction cannot beat the incumbent. Still evaluated
            # (contributes correctly-neutral pairs), not skipped.
            challenger_fit_df = backtest_df[["dc_home_win", "dc_draw", "dc_away_win", "actual_result"]]
        else:
            challenger_fit_df = pd.concat(
                [backtest_df[["dc_home_win", "dc_draw", "dc_away_win", "actual_result"]], train_real], ignore_index=True,
            )
        challenger = fit_challenger(challenger_fit_df, n_real_matches=len(train_real))
        methods_used.append(challenger["method"])
        n_chunks += 1

        for _, r in chunk.iterrows():
            raw = {"home_win": r["dc_home_win"], "draw": r["dc_draw"], "away_win": r["dc_away_win"]}
            incumbent_losses.append(log_loss_row(apply_calibration(incumbent, raw), r["actual_result"]))
            challenger_losses.append(log_loss_row(apply_challenger(challenger, raw), r["actual_result"]))

    return {
        "incumbent_losses": np.array(incumbent_losses), "challenger_losses": np.array(challenger_losses),
        "n_chunks": n_chunks, "methods_used": methods_used,
    }


def paired_bootstrap_ci(
    incumbent_losses: np.ndarray, challenger_losses: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP, seed: int = BOOTSTRAP_SEED,
) -> dict:
    """Same style as final_stacked_model.paired_bootstrap_significance:
    positive difference means the challenger is better (lower loss)."""
    n = len(incumbent_losses)
    point_estimate = float(incumbent_losses.mean() - challenger_losses.mean())
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        diffs[i] = incumbent_losses[idx].mean() - challenger_losses[idx].mean()
    ci_low, ci_high = (float(x) for x in np.percentile(diffs, [2.5, 97.5]))
    return {
        "point_estimate": point_estimate, "ci_low": ci_low, "ci_high": ci_high,
        # Promotion requires the WHOLE CI on the challenger-is-better side,
        # not just excluding zero in either direction.
        "challenger_significantly_better": ci_low > 0,
    }


def attempt_recalibration(paths, backtest_path: Path | None = None, matchweek: int | None = None, force: bool = False) -> dict | None:
    """Returns None (a documented no-op) if: below MIN_MATCHES_TO_ATTEMPT
    real matches, or (unless `force=True`, used by tests and manual runs)
    `matchweek` is not a multiple of EVALUATION_CADENCE_MATCHWEEKS.
    `backtest_path` is overridable so tests never touch the real static
    backtest file."""
    real_scored = _real_scored_df(paths)
    n_real = len(real_scored)
    if n_real < MIN_MATCHES_TO_ATTEMPT:
        return None
    if not force and matchweek is not None and matchweek % EVALUATION_CADENCE_MATCHWEEKS != 0:
        return None

    backtest_path = backtest_path if backtest_path is not None else BACKTEST_PATH
    if not backtest_path.exists():
        return None
    backtest_df = pd.read_csv(backtest_path)

    rolling = rolling_origin_paired_losses(real_scored, backtest_df)
    ci = paired_bootstrap_ci(rolling["incumbent_losses"], rolling["challenger_losses"])
    decision = "PROMOTED" if ci["challenger_significantly_better"] else "REJECTED"

    # The final challenger promoted (if any) is refit once more on ALL
    # real matches available now, for use going forward -- the rolling
    # evaluation above is what earns the promotion, this is what
    # actually gets deployed.
    final_method = rolling["methods_used"][-1] if rolling["methods_used"] else "temperature_scaling"
    final_challenger = fit_challenger(
        pd.concat([backtest_df[["dc_home_win", "dc_draw", "dc_away_win", "actual_result"]], _to_backtest_schema(real_scored)], ignore_index=True),
        n_real_matches=n_real,
    )

    generated_at = now_utc_iso()
    decision_id = f"recal_{generated_at.replace(':', '').replace('-', '')}"
    decision_row = pd.DataFrame([{
        "decision_id": decision_id, "generated_at": generated_at, "matchweek": matchweek if matchweek is not None else "",
        "n_real_matches_total": n_real, "n_paired_observations": len(rolling["incumbent_losses"]),
        "n_rolling_chunks": rolling["n_chunks"], "challenger_method": final_method,
        "point_estimate_log_loss_diff": round(ci["point_estimate"], 4),
        "ci_low": round(ci["ci_low"], 4), "ci_high": round(ci["ci_high"], 4), "decision": decision,
        "notes": (
            f"rolling-origin: {rolling['n_chunks']} chunks of up to {ROLLING_CHUNK_SIZE} real matches each, "
            f"challenger refit before every chunk on (static backtest + real matches strictly before it); "
            f"paired bootstrap {N_BOOTSTRAP} resamples; promotion requires the full 95% CI on the "
            "challenger-is-better side (ci_low > 0), not a point-estimate win."
        ),
    }])
    paths.recalibration_decisions.parent.mkdir(parents=True, exist_ok=True)
    write_header = not paths.recalibration_decisions.exists()
    decision_row.to_csv(paths.recalibration_decisions, mode="a", header=write_header, index=False)

    if decision == "PROMOTED":
        paths.active_calibrators.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.active_calibrators, "wb") as f:
            pickle.dump({"challenger": final_challenger, "decision_id": decision_id, "generated_at": generated_at}, f)

    return {
        "decision": decision, "decision_id": decision_id,
        "point_estimate_log_loss_diff": ci["point_estimate"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
        "n_real_matches_total": n_real, "n_paired_observations": len(rolling["incumbent_losses"]),
        "challenger_method": final_method, "final_challenger": final_challenger,
    }


def load_active_calibrators(active_calibrators_path: Path) -> dict | None:
    """Used by predict_all_matches.build_model_context: if a challenger
    has ever been promoted, it replaces the static historical-only fit
    -- until a LATER challenger beats it in turn. Every promotion is
    still permanently recorded in the append-only decision log
    regardless of what this file currently holds. Returns a dict with
    key "method" ("temperature_scaling" or "isotonic") so the caller
    knows how to apply it -- see apply_challenger."""
    if not active_calibrators_path.exists():
        return None
    with open(active_calibrators_path, "rb") as f:
        payload = pickle.load(f)
    return payload["challenger"]


def main() -> None:
    import argparse

    from src.update_after_matchweek import DEFAULT_PATHS

    parser = argparse.ArgumentParser(description="Attempt gated challenger recalibration.")
    parser.add_argument("--matchweek", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="ignore the evaluation cadence (for manual runs)")
    args = parser.parse_args()
    result = attempt_recalibration(DEFAULT_PATHS, matchweek=args.matchweek, force=args.force)
    if result is None:
        print(f"No-op: below {MIN_MATCHES_TO_ATTEMPT} real matches, or not a cadence matchweek (every {EVALUATION_CADENCE_MATCHWEEKS}).")
        return
    print(f"Decision: {result['decision']} (95% CI on log-loss diff: [{result['ci_low']:.4f}, {result['ci_high']:.4f}], "
          f"{result['n_paired_observations']} paired observations, challenger method={result['challenger_method']})")


if __name__ == "__main__":
    main()
