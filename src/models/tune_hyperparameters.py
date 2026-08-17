"""Optuna hyperparameter search for the Dixon-Coles and Elo models.

**Tuning objective simplification** (documented, not hidden): the full
rolling-origin backtest (src/evaluation/backtest.py) refits Dixon-Coles
~38 times per validation season and takes ~12 minutes for 7 seasons --
too slow to run as the inner loop of a hyperparameter search (even 20
trials would take hours). Instead, each trial here does a **single
preseason-style fit** on all data through 2024/25 and evaluates it
against the entirety of the real, held-out 2025/26 season (380
matches, no leakage -- the fit never sees 2025/26 results). This is
actually a closer match to how the model is really used for a new
season's predictions (one preseason fit) than the walk-forward
backtest is, and it makes each trial take ~1 fit (~1-25s) instead of
~38.

The final tuned hyperparameters are written to
`config/model_config.yaml` (with the previous file backed up) and
should be followed by a fresh run of the full backtest
(src/evaluation/backtest.py) for final, walk-forward-validated
reporting -- this script does not replace that backtest, only feeds it
better starting hyperparameters.

Optimization target: primary = mean log loss on the 2025/26 holdout
(spec-required primary metric); Brier score is also recorded per trial
for secondary reference.

Run: python -m src.models.tune_hyperparameters [--n-trials 30]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.baselines import elo_only_probabilities  # noqa: E402
from src.models.scoreline_models import (  # noqa: E402
    fit_dixon_coles_model,
    match_lambdas,
    outcome_probabilities,
    score_matrix,
)
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
OUT_TUNING_LOG = REPO_ROOT / "data" / "outputs" / "epl_hyperparameter_tuning_trials.csv"
OUT_TUNING_REPORT = REPO_ROOT / "reports" / "epl_hyperparameter_tuning_report.md"

HOLDOUT_SEASON = "2025-26"
RESULT_ORDER = ["away_win", "draw", "home_win"]


def _log_loss(probs: dict, actual: str) -> float:
    return -np.log(max(probs[actual], 1e-12))


def _brier(probs: dict, actual: str) -> float:
    return sum((probs[c] - (1.0 if c == actual else 0.0)) ** 2 for c in RESULT_ORDER)


def evaluate_dixon_coles(df_train: pd.DataFrame, holdout: pd.DataFrame, universe: list[str], half_life_days: float, l2_reg: float) -> tuple[float, float]:
    as_of_date = holdout["date"].min()
    fit = fit_dixon_coles_model(df_train, universe, as_of_date, half_life_days=half_life_days, l2_reg=l2_reg)

    losses, briers = [], []
    for _, m in holdout.iterrows():
        home, away = m["home_team"], m["away_team"]
        if home not in fit.team_index or away not in fit.team_index:
            continue
        lam, mu = match_lambdas(fit, home, away)
        matrix = score_matrix(lam, mu, fit.rho)
        h, d, a = outcome_probabilities(matrix)
        probs = {"home_win": h, "draw": d, "away_win": a}
        actual = "home_win" if m["home_goals"] > m["away_goals"] else ("draw" if m["home_goals"] == m["away_goals"] else "away_win")
        losses.append(_log_loss(probs, actual))
        briers.append(_brier(probs, actual))
    return float(np.mean(losses)), float(np.mean(briers))


def evaluate_elo(df_train: pd.DataFrame, holdout: pd.DataFrame, k_factor: float, home_advantage: float) -> tuple[float, float]:
    """Single sequential Elo pass over train+holdout (not re-run per holdout
    match -- that would mean ~380 full-history passes per trial, far too
    slow for a hyperparameter search). Elo's `history` already gives each
    match its pre-match rating (computed from strictly earlier matches
    only), which is exactly what leakage-safe evaluation needs -- see the
    identical technique in src/evaluation/backtest.py."""
    offset, _ = compute_promoted_team_elo_offset(df_train)
    combined = pd.concat([df_train, holdout]).sort_values("date").reset_index(drop=True)
    run = run_elo(combined, promoted_offset=offset, k_factor=k_factor, home_advantage=home_advantage)
    history = run.history
    history = history[history["date"] >= holdout["date"].min()]

    losses, briers = [], []
    for _, row in history.iterrows():
        h, d, a = elo_only_probabilities(row["home_elo_pre"], row["away_elo_pre"], home_advantage)
        probs = {"home_win": h, "draw": d, "away_win": a}
        match = holdout[(holdout["date"] == row["date"]) & (holdout["home_team"] == row["home_team"]) & (holdout["away_team"] == row["away_team"])]
        if match.empty:
            continue
        m = match.iloc[0]
        actual = "home_win" if m["home_goals"] > m["away_goals"] else ("draw" if m["home_goals"] == m["away_goals"] else "away_win")
        losses.append(_log_loss(probs, actual))
        briers.append(_brier(probs, actual))
    return float(np.mean(losses)), float(np.mean(briers))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-trials", type=int, default=25)
    args = parser.parse_args()

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)
    hist_teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    holdout = df[df["season"] == HOLDOUT_SEASON].sort_values("date").reset_index(drop=True)
    train = df[df["date"] < holdout["date"].min()]
    print(f"Tuning against held-out season {HOLDOUT_SEASON}: {len(holdout)} real matches, "
          f"{len(train)} real training matches strictly before it.")

    trial_log = []

    def dc_objective(trial: optuna.Trial) -> float:
        half_life = trial.suggest_float("half_life_days", 150, 700)
        l2_reg = trial.suggest_float("l2_reg", 0.005, 0.15, log=True)
        log_loss, brier = evaluate_dixon_coles(train, holdout, universe, half_life, l2_reg)
        trial_log.append({"model": "dixon_coles", "trial": trial.number, "half_life_days": half_life, "l2_reg": l2_reg, "log_loss": log_loss, "brier": brier})
        return log_loss

    print(f"\nRunning {args.n_trials} Optuna trials for Dixon-Coles (half_life_days, l2_reg)...")
    dc_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=20260818))
    dc_study.optimize(dc_objective, n_trials=args.n_trials, show_progress_bar=False)
    print(f"Best Dixon-Coles: {dc_study.best_params}, log_loss={dc_study.best_value:.4f}")

    def elo_objective(trial: optuna.Trial) -> float:
        k = trial.suggest_float("k_factor", 8, 40)
        home_adv = trial.suggest_float("home_advantage_elo_points", 20, 100)
        log_loss, brier = evaluate_elo(train, holdout, k, home_adv)
        trial_log.append({"model": "elo", "trial": trial.number, "k_factor": k, "home_advantage_elo_points": home_adv, "log_loss": log_loss, "brier": brier})
        return log_loss

    print(f"\nRunning {args.n_trials} Optuna trials for Elo (k_factor, home_advantage)...")
    elo_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=20260818))
    elo_study.optimize(elo_objective, n_trials=args.n_trials, show_progress_bar=False)
    print(f"Best Elo: {elo_study.best_params}, log_loss={elo_study.best_value:.4f}")

    pd.DataFrame(trial_log).to_csv(OUT_TUNING_LOG, index=False)
    print(f"\nWrote {len(trial_log)} trial records to {OUT_TUNING_LOG}")

    with open(MODEL_CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    baseline_dc_loss, _ = evaluate_dixon_coles(train, holdout, universe, cfg["dixon_coles"]["time_decay_half_life_days"], 0.03)
    baseline_elo_loss, _ = evaluate_elo(train, holdout, cfg["elo"]["k_factor"], cfg["elo"]["home_advantage_elo_points"])

    shutil.copy(MODEL_CONFIG_PATH, MODEL_CONFIG_PATH.with_suffix(".yaml.pre_tuning_backup"))
    cfg["dixon_coles"]["time_decay_half_life_days"] = round(dc_study.best_params["half_life_days"], 1)
    cfg["dixon_coles"]["l2_reg"] = round(dc_study.best_params["l2_reg"], 4)
    cfg["elo"]["k_factor"] = round(elo_study.best_params["k_factor"], 1)
    cfg["elo"]["home_advantage_elo_points"] = round(elo_study.best_params["home_advantage_elo_points"], 1)
    cfg["tuning"] = {
        "tuned_at": now_utc_iso(),
        "holdout_season": HOLDOUT_SEASON,
        "n_trials_per_model": args.n_trials,
        "dc_holdout_log_loss_before": round(baseline_dc_loss, 4),
        "dc_holdout_log_loss_after": round(dc_study.best_value, 4),
        "elo_holdout_log_loss_before": round(baseline_elo_loss, 4),
        "elo_holdout_log_loss_after": round(elo_study.best_value, 4),
    }
    with open(MODEL_CONFIG_PATH, "w") as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)
    print(f"\nUpdated {MODEL_CONFIG_PATH} with tuned hyperparameters (previous version backed up alongside it).")

    with open(OUT_TUNING_REPORT, "w") as f:
        f.write("# EPL Hyperparameter Tuning Report (Phase 2)\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(f"Held out real season: **{HOLDOUT_SEASON}** ({len(holdout)} matches). Trained on all real "
                f"matches strictly before it ({len(train)} matches). Each trial fits once and evaluates "
                f"log loss over the full holdout season -- see the module docstring for why this differs "
                f"from the full walk-forward backtest.\n\n")
        f.write("## Dixon-Coles\n\n")
        f.write(f"- Trials: {args.n_trials}\n")
        f.write(f"- Baseline (previous config) holdout log loss: {baseline_dc_loss:.4f}\n")
        f.write(f"- Best found: half_life_days={dc_study.best_params['half_life_days']:.1f}, "
                f"l2_reg={dc_study.best_params['l2_reg']:.4f} -> holdout log loss {dc_study.best_value:.4f}\n\n")
        f.write("## Elo\n\n")
        f.write(f"- Trials: {args.n_trials}\n")
        f.write(f"- Baseline (previous config) holdout log loss: {baseline_elo_loss:.4f}\n")
        f.write(f"- Best found: k_factor={elo_study.best_params['k_factor']:.1f}, "
                f"home_advantage_elo_points={elo_study.best_params['home_advantage_elo_points']:.1f} "
                f"-> holdout log loss {elo_study.best_value:.4f}\n\n")
        f.write("## Next step\n\n"
                "`config/model_config.yaml` has been updated with these values. Re-run "
                "`src/evaluation/backtest.py`, `src/calibration/calibrate_probabilities.py`, "
                "`src/simulation/simulate_full_season.py`, and `src/models/predict_all_matches.py` "
                "to regenerate all downstream outputs with the tuned hyperparameters.\n")
    print(f"Wrote tuning report to {OUT_TUNING_REPORT}")

    meta = make_run_metadata(
        prefix="tune", season="2026-27",
        hyperparameters=json.dumps({"dixon_coles": dc_study.best_params, "elo": elo_study.best_params}),
        metrics=json.dumps({"dc_log_loss": dc_study.best_value, "elo_log_loss": elo_study.best_value}),
    )
    log_experiment(meta, stage="hyperparameter_tuning", notes=f"{args.n_trials} trials/model, holdout={HOLDOUT_SEASON}")


if __name__ == "__main__":
    main()
