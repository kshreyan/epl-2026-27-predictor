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
its own output.

**Whether the ensemble is used is decided by a paired bootstrap
significance test, not a raw point-estimate comparison.** An earlier
version of this module declared the ensemble "primary" on a 0.0031
log-loss point-estimate gap alone (0.9865 vs 0.9834) -- on ~2,660
matches the standard error of that estimate is comparable to the gap
itself, so the point estimate could not actually support that claim.
A paired bootstrap (10,000 resamples over matches, since both models
score the same matches) puts the 95% CI on the difference at
[-0.0021, +0.0087] -- straddling zero -- and the ensemble wins only 3
of 7 individual seasons. Both facts say this is noise, not signal.
`ensemble_beats_dc` therefore requires BOTH the bootstrap CI to
exclude zero AND the ensemble to win a majority of seasons, computed
fresh every time this module runs (not hardcoded), so a real future
improvement can still turn the ensemble on without a code change, and
a regression turns it back off automatically.

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
OUT_PER_SEASON = REPO_ROOT / "data" / "outputs" / "epl_ensemble_per_season_comparison.csv"

BASE_MODELS = ["dc", "elo", "prevseason", "simplepoisson"]
CLASSES = ["away_win", "draw", "home_win"]  # fixed order for the meta-learner's label encoding
N_FOLDS = 5
RESULT_ORDER = ["away_win", "draw", "home_win"]
N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 20260818


def _feature_matrix(df: pd.DataFrame) -> np.ndarray:
    cols = [f"{m}_{c}" for m in BASE_MODELS for c in ("home_win", "draw", "away_win")]
    return df[cols].to_numpy()


def _log_loss(probs: np.ndarray, actual_idx: np.ndarray) -> float:
    p = np.clip(probs[np.arange(len(actual_idx)), actual_idx], 1e-12, 1.0)
    return float(-np.mean(np.log(p)))


def _log_loss_per_row(probs: np.ndarray, actual_idx: np.ndarray) -> np.ndarray:
    p = np.clip(probs[np.arange(len(actual_idx)), actual_idx], 1e-12, 1.0)
    return -np.log(p)


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


def paired_bootstrap_significance(
    dc_loss: np.ndarray, ensemble_loss: np.ndarray, seasons: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP, seed: int = BOOTSTRAP_SEED,
) -> dict:
    """Paired bootstrap (same resampled matches score both models) plus a
    per-season win/loss breakdown. Returns everything needed to decide
    (and report) whether the ensemble's apparent edge is real."""
    n = len(dc_loss)
    point_estimate = float(dc_loss.mean() - ensemble_loss.mean())  # positive => ensemble better

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        diffs[i] = dc_loss[idx].mean() - ensemble_loss[idx].mean()
    ci_low, ci_high = (float(x) for x in np.percentile(diffs, [2.5, 97.5]))
    ci_excludes_zero = not (ci_low <= 0 <= ci_high)

    per_season = []
    season_wins = 0
    for season in pd.unique(seasons):
        mask = seasons == season
        dc_mean, ens_mean = float(dc_loss[mask].mean()), float(ensemble_loss[mask].mean())
        wins = ens_mean < dc_mean
        season_wins += int(wins)
        per_season.append({"season": season, "n_matches": int(mask.sum()), "dc_log_loss": round(dc_mean, 4),
                            "ensemble_log_loss": round(ens_mean, 4), "ensemble_wins_season": wins})
    n_seasons = len(per_season)
    season_majority = season_wins > n_seasons / 2

    return {
        "point_estimate": point_estimate, "ci_low": ci_low, "ci_high": ci_high,
        "ci_excludes_zero": ci_excludes_zero, "fraction_favoring_ensemble": float((diffs > 0).mean()),
        "per_season": pd.DataFrame(per_season).sort_values("season"),
        "season_wins": season_wins, "n_seasons": n_seasons, "season_majority": season_majority,
        "ensemble_significant": bool(ci_excludes_zero and season_majority),
    }


def run_oof_stacking(backtest_df: pd.DataFrame) -> tuple[pd.DataFrame, LogisticRegression, dict, dict]:
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

    ens_loss_per_row = _log_loss_per_row(oof_probs, y)
    significance = paired_bootstrap_significance(
        backtest_df["dc_log_loss"].to_numpy(), ens_loss_per_row, backtest_df["season"].to_numpy(),
    )

    oof_df = backtest_df[["season", "date", "home_team", "away_team", "actual_result"]].copy()
    for i, c in enumerate(CLASSES):
        oof_df[f"ensemble_{c}"] = oof_probs[:, i]
    return oof_df, final_meta, metrics, significance


def fit_final_meta_learner(backtest_df: pd.DataFrame) -> tuple[LogisticRegression, bool, dict]:
    """Reusable entry point for other modules (predict_all_matches.py):
    returns the meta-learner fit on all real backtest data, whether its
    edge over Dixon-Coles alone is statistically significant (paired
    bootstrap CI excludes zero AND it wins a majority of seasons -- not
    just a point-estimate comparison), and the comparison metrics."""
    _, final_meta, metrics, significance = run_oof_stacking(backtest_df)
    metrics["bootstrap_ci_low"] = significance["ci_low"]
    metrics["bootstrap_ci_high"] = significance["ci_high"]
    metrics["season_wins"] = significance["season_wins"]
    metrics["n_seasons"] = significance["n_seasons"]
    return final_meta, significance["ensemble_significant"], metrics


def main() -> None:
    if not BACKTEST_PATH.exists():
        raise FileNotFoundError(f"{BACKTEST_PATH} not found -- run src/evaluation/backtest.py first")
    backtest_df = pd.read_csv(BACKTEST_PATH)

    oof_df, final_meta, metrics, significance = run_oof_stacking(backtest_df)
    oof_df.to_csv(OUT_OOF_PREDICTIONS, index=False)
    print(f"Wrote {len(oof_df)} out-of-fold ensemble predictions to {OUT_OOF_PREDICTIONS}")
    significance["per_season"].to_csv(OUT_PER_SEASON, index=False)

    beats_dc = significance["ensemble_significant"]
    coef_df = pd.DataFrame(
        final_meta.coef_,
        index=[CLASSES[c] for c in final_meta.classes_],
        columns=[f"{m}_{c}" for m in BASE_MODELS for c in ("home_win", "draw", "away_win")],
    )

    with open(OUT_REPORT, "w") as f:
        f.write("# EPL 2026-27 Stacked Ensemble Report (Phase 3, revised)\n\n")
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
        f.write("## Statistical significance (paired bootstrap, 10,000 resamples)\n\n")
        f.write(f"- Point estimate (DC log loss − ensemble log loss): {significance['point_estimate']:+.4f} "
                f"(positive = ensemble better)\n")
        f.write(f"- 95% CI: [{significance['ci_low']:+.4f}, {significance['ci_high']:+.4f}] "
                f"({'excludes zero' if significance['ci_excludes_zero'] else '**straddles zero**'})\n")
        f.write(f"- Per-season: ensemble wins {significance['season_wins']}/{significance['n_seasons']} seasons\n\n")
        f.write(significance["per_season"].to_markdown(index=False))
        f.write("\n\n")
        if beats_dc:
            f.write("**The ensemble's edge is statistically significant (bootstrap CI excludes zero AND it wins "
                    "a season majority) and it is used for the final 2026-27 predictions.**\n\n")
        else:
            f.write("**The ensemble's apparent edge is NOT statistically significant on this evidence "
                    "(bootstrap CI straddles zero and/or it does not win a season majority) -- Dixon-Coles "
                    "alone remains the primary model.** A prior version of this report declared the ensemble "
                    "primary from a raw 0.0031 log-loss point-estimate gap with no significance test; that "
                    "was wrong, and this decision now requires both criteria above, computed fresh every "
                    "time this module runs.\n\n")
        f.write("## Meta-learner coefficients\n\n")
        f.write(coef_df.round(3).to_markdown())
        f.write("\n\n## Limitations\n\n"
                "- Only 4 of the 11 sub-models envisioned by the full spec exist with real data (player-minutes, "
                "squad-injury, transfer-impact, market, and tactical-style models are all blocked on unconnected "
                "data sources -- see `reports/epl_2026_27_model_report.md`).\n"
                "- The meta-learner's own hyperparameter (L2 strength C=1.0) was not separately tuned.\n"
                "- The significance decision rule (CI excludes zero AND season majority) is a reasonable but "
                "not uniquely-correct threshold; a single-season swing could still flip the majority vote.\n")

    print(f"Wrote ensemble report to {OUT_REPORT}")
    print(f"Ensemble edge is {'SIGNIFICANT -- using ensemble' if beats_dc else 'NOT significant -- using Dixon-Coles alone'} "
          f"(95% CI [{significance['ci_low']:+.4f}, {significance['ci_high']:+.4f}], "
          f"{significance['season_wins']}/{significance['n_seasons']} seasons)")

    meta_run = make_run_metadata(
        prefix="ensemble", season="2026-27",
        metrics=json.dumps({k: v for k, v in metrics.items()}),
        hyperparameters=json.dumps({"n_folds": N_FOLDS, "meta_C": 1.0, "n_bootstrap": N_BOOTSTRAP}),
    )
    log_experiment(meta_run, stage="stacked_ensemble", notes=f"significant={beats_dc}, ci=[{significance['ci_low']:.4f},{significance['ci_high']:.4f}]")
    register_model(meta_run, model_name="stacked_ensemble_logreg", notes=json.dumps(metrics))


if __name__ == "__main__":
    main()
