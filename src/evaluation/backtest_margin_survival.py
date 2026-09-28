"""Rolling-origin calibration backtest for the +2 Margin Survival Engine
(src/models/compute_margin_survival.py).

Reuses the exact same rolling-origin discipline as backtest.py (refit
Dixon-Coles roughly every real matchweek, using only matches strictly
before that point -- no random splitting, no future data) but scores a
different target: not moneyline log loss, but calibration of
P(lose by 3+) specifically, per the master spec's mandatory calibration
requirement ("if the system labels 100 teams as having a 5% probability
of losing by 3+, approximately five should actually lose by 3+").

Only run over matches whose real, pre-kickoff modal score was eligible
(0-1, 1-0, or a draw) -- the same eligibility gate the live engine uses
-- so the backtest measures calibration on exactly the population the
site actually publishes, not on blowout-obvious fixtures no one would
ever look at +2 for.

Run: python -m src.evaluation.backtest_margin_survival [--league epl]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import CHUNK_SIZE, HALF_LIFE_DAYS, L2_REG, VALIDATION_SEASONS, _paths  # noqa: E402
from src.models.compute_margin_survival import ELIGIBLE_DRAWS_AND, margin_buckets  # noqa: E402
from src.models.promoted_team_adjustment import (  # noqa: E402
    compute_promoted_team_history,
    summarize_promoted_team_baseline,
)
from src.models.scoreline_models import (  # noqa: E402
    apply_promoted_team_adjustment,
    fit_dixon_coles_model,
    match_lambdas,
    score_matrix,
)
from src.utils.versioning import log_experiment, make_run_metadata  # noqa: E402

MARGIN_SURVIVAL_LEAGUE_IDS = ["epl", "la_liga", "serie_a", "bundesliga", "ligue_1"]
CALIBRATION_BUCKETS = [0.01, 0.03, 0.05, 0.075, 0.10, 0.15, 1.01]
BUCKET_LABELS = ["<1%", "1-3%", "3-5%", "5-7.5%", "7.5-10%", "10-15%", "15%+"]


def bucket_index(p_fail: float) -> int:
    for i, upper in enumerate(CALIBRATION_BUCKETS):
        if p_fail < upper:
            return i
    return len(CALIBRATION_BUCKETS) - 1


def run_backtest(league_id: str) -> pd.DataFrame:
    paths = _paths(league_id)
    df = pd.read_csv(paths["historical"], parse_dates=["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)
    hist_teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    current_fixtures = pd.read_csv(paths["fixtures"])
    teams_2627 = sorted(set(current_fixtures["home_team"]) | set(current_fixtures["away_team"]))
    universe = sorted(set(hist_teams) | set(teams_2627))

    all_seasons_in_order = list(dict.fromkeys(df.sort_values("date")["season"]))
    teams_by_season = {
        s: set(df[df["season"] == s]["home_team"]) | set(df[df["season"] == s]["away_team"])
        for s in all_seasons_in_order
    }

    rows = []
    dc_fit = None
    for season in VALIDATION_SEASONS:
        season_matches = df[df["season"] == season].sort_values("date").reset_index(drop=True)
        if season_matches.empty:
            continue

        season_idx = all_seasons_in_order.index(season)
        prev_season = all_seasons_in_order[season_idx - 1] if season_idx > 0 else None
        promoted_this_season = teams_by_season[season] - teams_by_season[prev_season] if prev_season else set()
        history_before_season = df[df["date"] < season_matches["date"].iloc[0]]
        promo_summary = summarize_promoted_team_baseline(compute_promoted_team_history(history_before_season))
        shortfall = promo_summary["mean_points_below_league_avg"] or -15.0
        season_attack_offset = shortfall / 100.0
        season_defense_offset = shortfall / 100.0

        n_chunks = int(np.ceil(len(season_matches) / CHUNK_SIZE))
        for c in range(n_chunks):
            chunk = season_matches.iloc[c * CHUNK_SIZE:(c + 1) * CHUNK_SIZE]
            if chunk.empty:
                continue
            as_of_date = chunk["date"].iloc[0]
            train_pool = df[df["date"] < as_of_date]
            if train_pool.empty:
                continue

            dc_fit = fit_dixon_coles_model(train_pool, universe, as_of_date, HALF_LIFE_DAYS, warm_start=dc_fit, l2_reg=L2_REG)
            dc_fit_for_predictions = (
                apply_promoted_team_adjustment(dc_fit, list(promoted_this_season), season_attack_offset, season_defense_offset)
                if promoted_this_season else dc_fit
            )

            for _, m in chunk.iterrows():
                home, away = m["home_team"], m["away_team"]
                if home not in dc_fit.team_index or away not in dc_fit.team_index:
                    continue
                hg, ag = int(m["home_goals"]), int(m["away_goals"])

                lam, mu = match_lambdas(dc_fit_for_predictions, home, away)
                matrix = score_matrix(lam, mu, dc_fit_for_predictions.rho)
                pred_ij = max(((i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])), key=lambda ij: matrix[ij[0], ij[1]])
                eligible = pred_ij in ELIGIBLE_DRAWS_AND or pred_ij[0] == pred_ij[1]
                if not eligible:
                    continue

                for perspective, team_goals, opp_goals in (("home", hg, ag), ("away", ag, hg)):
                    buckets = margin_buckets(matrix, perspective)
                    p_fail = buckets["lose_3"] + buckets["lose_4plus"]
                    actual_gd = team_goals - opp_goals
                    actual_fail = actual_gd <= -3
                    rows.append({
                        "season": season, "date": m["date"], "match_id": m["match_id"],
                        "team": home if perspective == "home" else away,
                        "p_fail": p_fail, "actual_fail": actual_fail,
                    })

    return pd.DataFrame(rows)


def calibration_report(results: pd.DataFrame) -> pd.DataFrame:
    results = results.copy()
    results["bucket"] = results["p_fail"].apply(bucket_index)
    rows = []
    for i, label in enumerate(BUCKET_LABELS):
        sub = results[results["bucket"] == i]
        if sub.empty:
            continue
        rows.append({
            "bucket": label, "n_matches": len(sub),
            "mean_predicted_p_fail": round(sub["p_fail"].mean(), 4),
            "empirical_fail_rate": round(sub["actual_fail"].mean(), 4),
        })
    return pd.DataFrame(rows)


def main(league_id: str | None = None) -> None:
    league_ids = [league_id] if league_id else MARGIN_SURVIVAL_LEAGUE_IDS
    for lid in league_ids:
        results = run_backtest(lid)
        out_path = REPO_ROOT / "data" / "outputs" / f"{lid}_margin_survival_backtest_results.csv"
        results.to_csv(out_path, index=False)

        brier = float(np.mean((results["p_fail"] - results["actual_fail"]) ** 2))
        eps = 1e-9
        log_loss = float(-np.mean(
            results["actual_fail"] * np.log(results["p_fail"].clip(eps, 1 - eps))
            + (1 - results["actual_fail"]) * np.log((1 - results["p_fail"]).clip(eps, 1 - eps))
        ))
        cal = calibration_report(results)
        cal_path = REPO_ROOT / "data" / "outputs" / f"{lid}_margin_survival_calibration.csv"
        cal.to_csv(cal_path, index=False)

        print(f"\n=== {lid}: margin-survival P(lose 3+) calibration ({len(results)} real team-match observations) ===")
        print(f"Brier score: {brier:.4f}  |  Log loss: {log_loss:.4f}  |  base rate: {results['actual_fail'].mean():.4f}")
        print(cal.to_string(index=False))

        meta = make_run_metadata(prefix="backtest_margin_survival", season="2026-27")
        log_experiment(meta, stage="backtest_margin_survival", notes=f"{lid}: brier={brier:.4f} log_loss={log_loss:.4f} n={len(results)}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default=None, dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
