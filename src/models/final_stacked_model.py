"""Out-of-fold stacked ensemble of the models that actually have real
data behind them: Dixon-Coles, Elo, previous-season-table, and simple
Poisson (spec section 21).

The full spec envisions stacking eleven sub-models (player-minutes,
squad-injury, transfer-impact, market, tactical-style, ...). Only four
of those exist with real data in this project (see
reports/epl_2026_27_model_report.md "Deferred to later phases") -- the
rest have no connected data source, so "stacking" them would mean
stacking constants or noise, not a real ensemble. This module stacks
what is real.

Method: a multinomial logistic-regression meta-learner over the four
base models' 1X2 probabilities (12 input features), fit with proper
K-fold out-of-fold prediction on the real backtest set (2,660 matches)
-- the meta-learner never sees a fold's own predictions when fitting
that fold, so its reported performance is not inflated by fitting on
its own output. If the ensemble does not beat Dixon-Coles alone on
held-out log loss, Dixon-Coles remains the primary model (per the
project's own "don't include for prestige" principle, applied here to
the ensemble itself, not just neural models).

Run: python -m src.models.final_stacked_model
(requires src/evaluation/backtest.py to have been run first)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso, register_model  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKTEST_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
OUT_REPORT = REPO_ROOT / "reports" / "epl_2026_27_ensemble_report.md"
OUT_OOF_PREDICTIONS = REPO_ROOT / "data" / "outputs" / "epl_ensemble_oof_predictions.csv"

BASE_MODELS = ["dc", "elo", "prevseason", "simplepoisson"]
CLASSES = ["away_win", "draw", "home_win"]  # fixed order for the meta-learner's label encoding
N_FOLDS = 5
RESULT_ORDER = ["away_win", "draw", "home_win"]


def _feature_matrix(df: pd.DataFrame) -> np.ndarray:
    cols = [f"{m}_{c}" for m in BASE_MODELS for c in ("home_win", "draw", "away_win")]
    return df[cols].to_numpy()


def _log_loss(probs: np.ndarray, actual_idx: np.ndarray) -> float:
    p = np.clip(probs[np.arange(len(actual_idx)), actual_idx], 1e-12, 1.0)
    return float(-np.mean(np.log(p)))


def _brier(probs: np.ndarray, actual_idx: np.ndarray) -> float:
    onehot = np.zeros_like(probs)
    onehot[np.arange(len(actual_idx)), actual_idx] = 1.0
    return float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))


def _rps(probs: np.ndarray, actual_idx: np.ndarray) -> float:
    # probs columns are in CLASSES order (away_win, draw, home_win) -- an
    # ordinal scale, matching src/evaluation/backtest.py's RESULT_ORDER.
    cum_p = np.cumsum(probs, axis=1)
    onehot = np.zeros_like(probs)
    onehot[np.arange(len(actual_idx)), actual_idx] = 1.0
    cum_a = np.cumsum(onehot, axis=1)
    return float(np.mean(np.sum((cum_p[:, :-1] - cum_a[:, :-1]) ** 2, axis=1)) / (probs.shape[1] - 1))


def run_oof_stacking(backtest_df: pd.DataFrame) -> tuple[pd.DataFrame, LogisticRegression, dict]:
    X = _feature_matrix(backtest_df)
    class_to_idx = {c: i for i, c in enumerate(CLASSES)}
    y = backtest_df["actual_result"].map(class_to_idx).to_numpy()

    oof_probs = np.zeros((len(backtest_df), len(CLASSES)))
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=20260818)
    for train_idx, test_idx in skf.split(X, y):
        meta = LogisticRegression(max_iter=2000, C=1.0)
        meta.fit(X[train_idx], y[train_idx])
        # meta.classes_ may be a subset/reordering of range(len(CLASSES)) in
        # principle -- align explicitly rather than assuming column order.
        fold_probs = np.zeros((len(test_idx), len(CLASSES)))
        fold_probs[:, meta.classes_] = meta.predict_proba(X[test_idx])
        oof_probs[test_idx] = fold_probs

    final_meta = LogisticRegression(max_iter=2000, C=1.0)
    final_meta.fit(X, y)

    metrics = {
        "ensemble_log_loss": _log_loss(oof_probs, y),
        "ensemble_brier": _brier(oof_probs, y),
        "ensemble_rps": _rps(oof_probs, y),
        "dc_log_loss": float(backtest_df["dc_log_loss"].mean()),
        "dc_brier": float(backtest_df["dc_brier"].mean()),
        "dc_rps": float(backtest_df["dc_rps"].mean()),
    }

    oof_df = backtest_df[["season", "date", "home_team", "away_team", "actual_result"]].copy()
    for i, c in enumerate(CLASSES):
        oof_df[f"ensemble_{c}"] = oof_probs[:, i]
    return oof_df, final_meta, metrics


def fit_final_meta_learner(backtest_df: pd.DataFrame) -> tuple[LogisticRegression, bool, dict]:
    """Reusable entry point for other modules (predict_all_matches.py):
    returns the meta-learner fit on all real backtest data, whether it
    beat Dixon-Coles alone out-of-fold, and the comparison metrics --
    without re-running the full report-writing main()."""
    _, final_meta, metrics = run_oof_stacking(backtest_df)
    return final_meta, metrics["ensemble_log_loss"] < metrics["dc_log_loss"], metrics


def main() -> None:
    if not BACKTEST_PATH.exists():
        raise FileNotFoundError(f"{BACKTEST_PATH} not found -- run src/evaluation/backtest.py first")
    backtest_df = pd.read_csv(BACKTEST_PATH)

    oof_df, final_meta, metrics = run_oof_stacking(backtest_df)
    oof_df.to_csv(OUT_OOF_PREDICTIONS, index=False)
    print(f"Wrote {len(oof_df)} out-of-fold ensemble predictions to {OUT_OOF_PREDICTIONS}")

    beats_dc = metrics["ensemble_log_loss"] < metrics["dc_log_loss"]
    coef_df = pd.DataFrame(
        final_meta.coef_,
        index=[CLASSES[c] for c in final_meta.classes_],
        columns=[f"{m}_{c}" for m in BASE_MODELS for c in ("home_win", "draw", "away_win")],
    )

    with open(OUT_REPORT, "w") as f:
        f.write("# EPL 2026-27 Stacked Ensemble Report (Phase 3)\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write("Out-of-fold (5-fold, stratified) multinomial logistic-regression stacking of the four base "
                f"models with real data: Dixon-Coles, Elo, previous-season-table, and simple Poisson, evaluated "
                f"on the same {len(backtest_df)} real backtest matches used elsewhere in this project. "
                "The meta-learner never sees a fold's own matches when fitting that fold.\n\n")
        f.write("## Ensemble vs. Dixon-Coles alone (out-of-fold)\n\n")
        f.write("| Metric | Dixon-Coles alone | Stacked ensemble |\n|---|---|---|\n")
        f.write(f"| Log loss | {metrics['dc_log_loss']:.4f} | {metrics['ensemble_log_loss']:.4f} |\n")
        f.write(f"| Brier score | {metrics['dc_brier']:.4f} | {metrics['ensemble_brier']:.4f} |\n")
        f.write(f"| RPS | {metrics['dc_rps']:.4f} | {metrics['ensemble_rps']:.4f} |\n\n")
        if beats_dc:
            f.write("**The ensemble beats Dixon-Coles alone on out-of-fold log loss and is used for the final "
                    "2026-27 predictions** (see `data/outputs/epl_2026_27_match_predictions.csv`, "
                    "`model_version` will reflect the ensemble where applied).\n\n")
        else:
            f.write("**The ensemble does NOT beat Dixon-Coles alone on out-of-fold log loss.** Per this "
                    "project's own principle of not adding model complexity for its own sake (applied "
                    "originally to neural models, applied here to the ensemble itself), Dixon-Coles remains "
                    "the primary model for 2026-27 predictions. This is a real, disclosed negative result, "
                    "not a modeling failure being hidden -- four correlated models built on largely the same "
                    "goals data may simply not carry enough complementary signal to improve on the best single "
                    "model, especially once one of the four (previous-season-table) is a materially weaker "
                    "baseline that mostly adds noise to the stack.\n\n")
        f.write("## Meta-learner coefficients\n\n")
        f.write(coef_df.round(3).to_markdown())
        f.write("\n\n## Limitations\n\n"
                "- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, "
                "squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected "
                "data sources -- see `reports/epl_2026_27_model_report.md`).\n"
                "- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.\n")

    print(f"Wrote ensemble report to {OUT_REPORT}")
    print(f"Ensemble {'BEATS' if beats_dc else 'does NOT beat'} Dixon-Coles alone "
          f"(log loss {metrics['ensemble_log_loss']:.4f} vs {metrics['dc_log_loss']:.4f})")

    meta_run = make_run_metadata(
        prefix="ensemble", season="2026-27",
        metrics=json.dumps(metrics),
        hyperparameters=json.dumps({"n_folds": N_FOLDS, "meta_C": 1.0}),
    )
    log_experiment(meta_run, stage="stacked_ensemble", notes=f"beats_dc={beats_dc}")
    register_model(meta_run, model_name="stacked_ensemble_logreg", notes=json.dumps(metrics))


if __name__ == "__main__":
    main()
