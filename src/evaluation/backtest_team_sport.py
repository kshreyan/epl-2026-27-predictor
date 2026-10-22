"""Rolling-origin backtest for NFL/NBA, real historical data (see
collect_espn_historical.py -- 5 real prior seasons each, 1,359 real
NFL games / 6,153 real NBA games).

Walks forward through every real historical game in chronological
order (across all 5 real seasons combined, not held out season by
season -- same discipline as the domestic soccer backtest), refitting
the point-margin model (src/models/point_margin_model.py) every
CHUNK_SIZE real games using only real data strictly before that point,
then scores that chunk. The very first chunk has no real prior data
and is not scored, same convention every other backtest in this
project uses.

Compares three real candidates, not one assumed winner:
- **Point-margin model** (Elo + the real fitted margin regression --
  see point_margin_model.py).
- **Elo-only, win-probability-via-logistic baseline** (the standard
  Elo formula this project already uses for soccer's Elo-only
  baseline, `elo_only_probabilities`) -- tests whether the extra
  margin-regression step actually helps over plain Elo win
  probability.
- **Flat/home-field-only baseline** -- every game predicted from the
  real historical home-win-rate alone, no team strength at all -- the
  floor any real model must clear.

Also reports the real historical margin-of-victory distribution
(mean, std, percentiles) -- NBA has no real betting "key numbers"
(confirmed via direct research, unlike NFL's real 3/7), so its +2-
Margin-Survival-equivalent threshold must come from this real
distribution, not an assumed number. See
compute_margin_survival_team_sport.py.

Run: python -m src.evaluation.backtest_team_sport --league nfl
(also accepts nba)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row, rps  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.baselines import elo_only_probabilities  # noqa: E402
from src.models.point_margin_model import fit_point_margin_model, outcome_probabilities  # noqa: E402

CHUNK_SIZE = 15
ALLOWS_TIES = {"nfl": True, "nba": False}
ELO_K_FACTOR = 20.0
# Below this, fitting a 2-parameter regression (slope, intercept) is
# numerically unstable (confirmed directly: too few, too-similar real
# elo_diff values make np.polyfit's SVD fail to converge) and not
# meaningful anyway -- same "too thin to compute" discipline as
# MIN_HISTORY_MATCHES elsewhere in this project.
MIN_TRAIN_GAMES = 30


def result_from_margin(margin: float, allows_ties: bool) -> str:
    if allows_ties and margin == 0:
        return "draw"
    return "home_win" if margin > 0 else "away_win"


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    allows_ties = ALLOWS_TIES[league_id]
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    out_match_results = REPO_ROOT / "data" / "outputs" / league_path(league_id, "backtest_match_results.csv")
    out_model_comparison = REPO_ROOT / "data" / "outputs" / league_path(league_id, "backtest_model_comparison.csv")
    out_report = REPO_ROOT / "reports" / f"{league_id}_model_selection_report.md"

    df = pd.read_csv(historical_path, parse_dates=["date"])
    df = df.dropna(subset=["home_score", "away_score"]).sort_values("date").reset_index(drop=True)

    rows = []
    n_chunks = int(np.ceil(len(df) / CHUNK_SIZE))
    for c in range(n_chunks):
        chunk = df.iloc[c * CHUNK_SIZE:(c + 1) * CHUNK_SIZE]
        if chunk.empty:
            continue
        as_of_date = chunk["date"].iloc[0]
        train_pool = df[df["date"] < as_of_date]
        if len(train_pool) < MIN_TRAIN_GAMES:
            continue

        pm_fit = fit_point_margin_model(train_pool, allows_ties=allows_ties, k_factor=ELO_K_FACTOR)
        flat_home_win_rate = float((train_pool["home_score"] > train_pool["away_score"]).mean())
        flat_draw_rate = float((train_pool["home_score"] == train_pool["away_score"]).mean()) if allows_ties else 0.0
        flat_away_win_rate = 1 - flat_home_win_rate - flat_draw_rate

        for _, m in chunk.iterrows():
            home, away = m["home_team"], m["away_team"]
            actual_margin = m["home_score"] - m["away_score"]
            actual = result_from_margin(actual_margin, allows_ties)

            r_home = pm_fit.elo_run.final_ratings.get(home, 1500.0)
            r_away = pm_fit.elo_run.final_ratings.get(away, 1500.0)
            mean = pm_fit.slope * (r_home - r_away) + pm_fit.intercept
            pm_h, pm_d, pm_a = outcome_probabilities(mean, pm_fit.sigma, allows_ties)

            elo_h_raw, elo_d_raw, elo_a_raw = elo_only_probabilities(r_home, r_away, home_advantage=0.0)
            if allows_ties:
                # elo_only_probabilities already returns a real draw band
                # (same formula soccer uses) -- reuse it unchanged.
                elo_h, elo_d, elo_a = elo_h_raw, elo_d_raw, elo_a_raw
            else:
                total = elo_h_raw + elo_a_raw
                elo_h, elo_d, elo_a = elo_h_raw / total, 0.0, elo_a_raw / total

            pm_probs = {"home_win": pm_h, "draw": pm_d, "away_win": pm_a}
            elo_probs = {"home_win": elo_h, "draw": elo_d, "away_win": elo_a}
            flat_probs = {"home_win": flat_home_win_rate, "draw": flat_draw_rate, "away_win": flat_away_win_rate}

            rows.append({
                "date": m["date"].strftime("%Y-%m-%d"), "home_team": home, "away_team": away,
                "actual_home_score": int(m["home_score"]), "actual_away_score": int(m["away_score"]),
                "actual_margin": int(actual_margin), "actual_result": actual,
                "pm_home_win": pm_h, "pm_draw": pm_d, "pm_away_win": pm_a, "pm_mean_margin": mean, "pm_sigma": pm_fit.sigma,
                "elo_home_win": elo_h, "elo_draw": elo_d, "elo_away_win": elo_a,
                "flat_home_win": flat_home_win_rate, "flat_draw": flat_draw_rate, "flat_away_win": flat_away_win_rate,
                "pm_log_loss": log_loss_row(pm_probs, actual), "pm_brier": brier_row(pm_probs, actual), "pm_rps": rps(pm_probs, actual),
                "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                "flat_log_loss": log_loss_row(flat_probs, actual), "flat_brier": brier_row(flat_probs, actual), "flat_rps": rps(flat_probs, actual),
            })

    match_results = pd.DataFrame(rows)
    out_match_results.parent.mkdir(parents=True, exist_ok=True)
    match_results.to_csv(out_match_results, index=False)
    print(f"Wrote {len(match_results)} real scored backtest games to {out_match_results}")

    comparison_rows = []
    for model in ["pm", "elo", "flat"]:
        comparison_rows.append({
            "model": {"pm": "Point-margin model (Elo + margin regression)", "elo": "Elo-only win probability", "flat": "Flat/home-field-only baseline"}[model],
            "n_matches": len(match_results),
            "log_loss": match_results[f"{model}_log_loss"].mean(),
            "brier_score": match_results[f"{model}_brier"].mean(),
            "ranked_probability_score": match_results[f"{model}_rps"].mean(),
        })
    comparison = pd.DataFrame(comparison_rows).sort_values("log_loss")
    comparison.to_csv(out_model_comparison, index=False)
    print(f"Wrote model comparison to {out_model_comparison}")

    # Real historical margin-of-victory distribution -- the basis for
    # NBA's +2-Margin-Survival-equivalent threshold (no real betting
    # "key number" exists for NBA, unlike NFL's real 3/7 -- see
    # compute_margin_survival_team_sport.py).
    abs_margin = (df["home_score"] - df["away_score"]).abs()
    margin_percentiles = {p: float(np.percentile(abs_margin, p)) for p in [50, 60, 70, 75, 80, 85, 90]}

    best = comparison.iloc[0]
    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w") as f:
        f.write(f"# {cfg.display_name} Model Selection Report\n\n")
        f.write(
            f"Real rolling-origin backtest on {len(match_results)} real historical games "
            f"({df['date'].min().date()} to {df['date'].max().date()}, refit every {CHUNK_SIZE} real games using "
            f"only data strictly before that point -- no future leakage). Candidates compared honestly, not "
            f"assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-"
            f"victory regression, NOT soccer's Dixon-Coles/Poisson scoreline grid, which does not fit this "
            f"sport's scoring scale), a plain Elo-only win-probability baseline, and a flat/home-field-only "
            f"baseline.\n\n"
        )
        f.write("## Model comparison (lower log loss / Brier / RPS is better)\n\n")
        f.write(comparison.to_markdown(index=False))
        f.write(f"\n\n## Selected model\n\n**{best['model']}** has the lowest backtest log loss "
                f"({best['log_loss']:.4f}) and is used as the primary model for 2026-27 predictions.\n\n")
        f.write("## Real historical margin-of-victory distribution (absolute, points)\n\n")
        f.write("| Percentile | Absolute margin (points) |\n|---|---|\n")
        for p, v in margin_percentiles.items():
            f.write(f"| {p}th | {v:.1f} |\n")
        f.write(
            "\nUsed directly by compute_margin_survival_team_sport.py to set this league's real "
            "+2-Margin-Survival-equivalent threshold -- see that module's docstring for the exact choice and why.\n\n"
        )
        f.write(
            "## Limitations\n\n"
            "- Sample size is far smaller than this project's own 500-match isotonic-calibration minimum is "
            "meant for, but close to or above it for both sports (unlike the thin-sample UEFA club "
            "competitions) -- raw model probabilities are still used uncalibrated here for consistency with "
            "every other league in this project; calibration is a real, separate future improvement, not "
            "assumed to be unnecessary.\n"
            "- No historical market-odds source is wired in for either sport yet -- real current market odds "
            "(The Odds API) are shown alongside predictions for comparison only, not blended in.\n"
            "- Point-margin model ratings are held fixed between real games within this backtest's own refit "
            "cadence (every "
            f"{CHUNK_SIZE} games) -- a team's rating does not update mid-chunk, the same simplification the "
            "domestic soccer backtest makes between its own refit boundaries.\n"
        )
    print(f"Wrote model selection report to {out_report}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
