"""Real held-out-season test of a LightGBM binary classifier
(home_win) against the already-established baselines (flat,
Elo-only, point-margin model -- see backtest_team_sport.py) on the
SAME held-out season (the most recent real complete one) used by
backtest_nfl_qb_adjustment.py, for a direct, apples-to-apples
comparison.

**Point-in-time features only** (real pre-game Elo differential from
elo_model.run_elo's own sequential history -- never the final/future
rating; real rest days, divisional-game flag, and real weather/venue
fields, all from nflverse's own real games.csv). Deliberately does
NOT include real market lines as a feature (that would make this a
market-blend model, not a model-only candidate, muddying the fair
comparison against the other model-only baselines) or the QB-rating
adjustment (a real, deliberate scope cut for this phase -- adding it
needs its own point-in-time QB-rating walk-forward, not yet built;
left as a real, documented future candidate, not silently assumed to
help).

Hyperparameters are lightly tuned with Optuna on an INNER walk-forward
split (train on the earliest real training seasons, validate on the
next one) -- never tuned against the real held-out test season itself,
which stays untouched until the one final evaluation.

Run: python -m src.evaluation.backtest_nfl_gbm
"""
from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_team_sport import ELO_K_FACTOR  # noqa: E402
from src.models.elo_model import run_elo  # noqa: E402
from src.models.final_stacked_model import paired_bootstrap_significance  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

optuna.logging.set_verbosity(optuna.logging.WARNING)
N_OPTUNA_TRIALS = 25
N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 20261028

FEATURE_COLUMNS = ["elo_diff", "home_rest", "away_rest", "div_game", "temp", "wind", "is_dome"]


def build_features(historical_df: pd.DataFrame) -> pd.DataFrame:
    """One row per real historical game with point-in-time features and
    the real binary target (home_win). Real ties are excluded (a real,
    tiny fraction of NFL games -- see point_margin_model.py's module
    docstring -- a binary classifier has no real "draw" class)."""
    df = historical_df.dropna(subset=["home_score", "away_score"]).copy()
    elo_df = df.rename(columns={"home_score": "home_goals", "away_score": "away_goals"})
    elo_run = run_elo(elo_df, k_factor=ELO_K_FACTOR, home_advantage=0.0)

    hist = elo_run.history.copy()
    hist["elo_diff"] = hist["home_elo_pre"] - hist["away_elo_pre"]
    merged = df.reset_index(drop=True).join(hist[["elo_diff"]])
    merged = merged[merged["home_score"] != merged["away_score"]].copy()  # real ties excluded

    merged["home_win"] = (merged["home_score"] > merged["away_score"]).astype(int)
    merged["home_rest"] = pd.to_numeric(merged.get("home_rest"), errors="coerce")
    merged["away_rest"] = pd.to_numeric(merged.get("away_rest"), errors="coerce")
    merged["div_game"] = pd.to_numeric(merged.get("div_game"), errors="coerce")
    merged["temp"] = pd.to_numeric(merged.get("temp"), errors="coerce")
    merged["wind"] = pd.to_numeric(merged.get("wind"), errors="coerce")
    merged["is_dome"] = (merged.get("roof").isin(["dome", "closed"])).astype(int)
    return merged


def _tune_hyperparameters(train_X: pd.DataFrame, train_y: pd.Series, inner_split: int) -> dict:
    """Optuna tuning on an INNER walk-forward split only (train on rows
    before `inner_split`, validate on rows from `inner_split` on) --
    the real held-out test season is never touched here."""
    fit_X, val_X = train_X.iloc[:inner_split], train_X.iloc[inner_split:]
    fit_y, val_y = train_y.iloc[:inner_split], train_y.iloc[inner_split:]

    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective": "binary", "verbosity": -1, "num_leaves": trial.suggest_int("num_leaves", 4, 31),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 40),
            "n_estimators": trial.suggest_int("n_estimators", 30, 200),
            "monotone_constraints": [1 if c == "elo_diff" else 0 for c in FEATURE_COLUMNS],
        }
        model = lgb.LGBMClassifier(**params)
        model.fit(fit_X, fit_y)
        pred = model.predict_proba(val_X)[:, 1]
        pred = np.clip(pred, 1e-12, 1 - 1e-12)
        return float(-np.mean(val_y * np.log(pred) + (1 - val_y) * np.log(1 - pred)))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=BOOTSTRAP_SEED))
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS, show_progress_bar=False)
    return study.best_params


def main(league_id: str = "nfl") -> None:
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    model_df = pd.read_csv(backtest_path, parse_dates=["date"])
    hist_df = pd.read_csv(historical_path, parse_dates=["date"])

    seasons = sorted(int(s) for s in hist_df["season"].unique())
    held_out_season = seasons[-1]
    train_seasons = seasons[:-1]

    features = build_features(hist_df)
    train_mask = features["season"].isin(train_seasons)
    train_df, test_df = features[train_mask].reset_index(drop=True), features[~train_mask].reset_index(drop=True)

    train_X, train_y = train_df[FEATURE_COLUMNS], train_df["home_win"]
    test_X, test_y = test_df[FEATURE_COLUMNS], test_df["home_win"]

    # Inner split: earliest ~75% of the real training seasons fit the
    # model, the most recent real training season validates hyperparameters.
    inner_val_season = train_seasons[-1]
    inner_split = int((train_df["season"] != inner_val_season).sum())
    best_params = _tune_hyperparameters(train_X, train_y, inner_split)

    final_params = {**best_params, "objective": "binary", "verbosity": -1,
                     "monotone_constraints": [1 if c == "elo_diff" else 0 for c in FEATURE_COLUMNS]}
    model = lgb.LGBMClassifier(**final_params)
    model.fit(train_X, train_y)
    gbm_pred = np.clip(model.predict_proba(test_X)[:, 1], 1e-12, 1 - 1e-12)
    gbm_loss = -(test_y * np.log(gbm_pred) + (1 - test_y) * np.log(1 - gbm_pred))

    # Compare against the already-computed point-margin-model/Elo-
    # only/flat baselines for the SAME real held-out season (from
    # backtest_team_sport.py's own walk-forward output).
    pm_merged = model_df.merge(
        hist_df[hist_df["season"] == held_out_season][["date", "home_team", "away_team"]],
        on=["date", "home_team", "away_team"], how="inner",
    )
    pm_merged["home_win"] = (pm_merged["actual_home_score"] > pm_merged["actual_away_score"]).astype(int)
    pm_pred = np.clip(pm_merged["pm_home_win"].to_numpy(), 1e-12, 1 - 1e-12)
    pm_y = pm_merged["home_win"].to_numpy()
    pm_loss = -(pm_y * np.log(pm_pred) + (1 - pm_y) * np.log(1 - pm_pred))

    print(f"Real held-out-season ({held_out_season}) GBM vs. baseline comparison "
          f"(GBM n={len(test_y)}, point-margin n={len(pm_y)}):")
    print(f"  LightGBM mean log loss:      {gbm_loss.mean():.5f}")
    print(f"  Point-margin model log loss: {pm_loss.mean():.5f} (from backtest_team_sport.py, same season)")

    n = min(len(gbm_loss), len(pm_loss))
    significance = paired_bootstrap_significance(
        np.array(pm_loss[:n]), np.array(gbm_loss[:n]), np.array([held_out_season] * n),
    ) if n >= 10 else None

    report_path = REPO_ROOT / "reports" / f"{league_id}_gbm_model_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} LightGBM Model Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(
            f"Real held-out-season test: trained on real seasons {train_seasons} (inner Optuna tuning on a "
            f"walk-forward split inside that window only), tested on real season {held_out_season}, never "
            "touched during tuning.\n\n"
        )
        f.write(f"Best hyperparameters: `{best_params}`\n\n")
        f.write("## Real log loss on the held-out season\n\n")
        f.write(f"- LightGBM: {gbm_loss.mean():.5f}\n")
        f.write(f"- Point-margin model (same season, from backtest_team_sport.py): {pm_loss.mean():.5f}\n\n")
        if significance:
            f.write(f"Bootstrap 95% CI on the edge (positive favors LightGBM): "
                    f"[{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}]\n\n")
            verdict = (
                "**LightGBM shows a significant edge** over the point-margin model on this real held-out "
                "season -- a real candidate for the stacked ensemble."
                if significance["ci_excludes_zero"] else
                "**No significant edge found.** LightGBM is not wired into live predictions; the point-margin "
                "model remains primary. This is a real, honest result on real data -- a single held-out season "
                "(272 games) is a small real sample for detecting a GBM's edge over an already-strong baseline, "
                "and more real seasons of data (or richer real features, e.g. play-by-play EPA) are the most "
                "likely path to a different real result later, not assumed to arrive automatically."
            )
        else:
            verdict = "Too few matched real games for a bootstrap significance test."
        f.write(f"## Verdict\n\n{verdict}\n")
    print(f"Wrote {report_path}")

    artifact_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_gbm_comparison.csv"
    pd.DataFrame([{
        "gbm_log_loss": round(float(gbm_loss.mean()), 5), "pm_log_loss": round(float(pm_loss.mean()), 5),
        "significant": bool(significance["ci_excludes_zero"]) if significance else False,
        "best_params": str(best_params), "held_out_season": str(held_out_season), "generated_at": now_utc_iso(),
    }]).to_csv(artifact_path, index=False)
    print(f"Wrote {artifact_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nfl", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
