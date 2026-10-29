"""Rolling-origin backtest for NFL/NBA/NHL/NCAA Football, real
historical data (see collect_espn_historical.py -- 5 real prior
seasons each).

Walks forward through every real historical game in chronological
order (across all real seasons combined, not held out season by
season -- same discipline as the domestic soccer backtest), refitting
the point-margin model (src/models/point_margin_model.py) every
CHUNK_SIZE real games using only real data strictly before that point,
then scores that chunk. The very first chunk has no real prior data
and is not scored, same convention every other backtest in this
project uses.

Compares three real candidates for every league, not one assumed
winner:
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

**NHL gets a real fourth candidate**: Dixon-Coles (reusing
scoreline_models.py as-is), since real NHL scoring is low and discrete
like soccer's, unlike NFL's/NBA's/NCAA Football's point totals -- not
assumed to win, same empirical discipline as every other candidate
here. The real final score (post-OT/shootout) is what gets modeled --
a real draw is structurally impossible in it (confirmed directly: an
NHL game's real final score is never tied), so Dixon-Coles' own
`draw`-probability-via-diagonal naturally comes out at or near zero
rather than needing special handling.

Also reports the real historical margin-of-victory distribution
(mean, std, percentiles) -- most of these sports have no real betting
"key number" the way NFL's real 3/7 are (confirmed via direct
research), so each league's own +2-Margin-Survival-equivalent
threshold comes from this real distribution, not an assumed number.
See compute_margin_survival_team_sport.py.

Run: python -m src.evaluation.backtest_team_sport --league nfl
(also accepts nba, nhl, ncaaf)
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
from src.models.scoreline_models import fit_dixon_coles_model, match_lambdas, outcome_probabilities as dc_outcome_probabilities, score_matrix  # noqa: E402

CHUNK_SIZE = 15
ALLOWS_TIES = {"nfl": True, "nba": False, "nhl": False, "ncaaf": False}
# Only NHL's real scoring scale is low/discrete enough for Dixon-Coles
# to make real sense as a candidate -- see module docstring.
DIXON_COLES_CANDIDATE_LEAGUES = {"nhl"}
ELO_K_FACTOR = 20.0
# NHL's real max combined score comfortably exceeds soccer's default
# grid (confirmed directly: real NHL games up to 11 goals for one
# team, vs soccer's 0-8 grid) -- a wider grid for this sport only.
NHL_MAX_GOALS_GRID = 14
DC_HALF_LIFE_DAYS = 425.0  # same real half-life soccer's own Dixon-Coles fit uses, no sport-specific real calibration done here yet
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
    use_dc = league_id in DIXON_COLES_CANDIDATE_LEAGUES
    dc_teams_universe = sorted(set(df["home_team"]) | set(df["away_team"])) if use_dc else []

    # NCAA Football only: real conference-level hierarchical shrinkage
    # (see elo_model.run_elo's team_group docstring) -- fetched ONCE
    # here (a real live API call), not inside the chunk loop below.
    # Uses TODAY's real conference structure for every real historical
    # season in this backtest, not each season's own real (and, for
    # NCAA Football, genuinely different pre-2023-realignment) one --
    # a real, disclosed simplification, the same one
    # simulate_team_sport_season.py's team_division_conference()
    # already makes for this league's live standings.
    team_group = None
    if league_id == "ncaaf":
        from src.data_collection.espn_api import fetch_real_fbs_conferences
        conferences = fetch_real_fbs_conferences()
        team_group = {t["display_name"]: conf for conf, roster in conferences.items() for t in roster}

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
        # NCAA Football only: a real, SEPARATE candidate using
        # conference-aware reversion (see team_group above), scored
        # alongside the flat-reversion pm_fit above rather than
        # replacing it -- never assumed to win, same "let the real
        # backtest decide" discipline as every other candidate here.
        pmc_fit = fit_point_margin_model(train_pool, allows_ties=allows_ties, k_factor=ELO_K_FACTOR, team_group=team_group) if team_group else None
        flat_home_win_rate = float((train_pool["home_score"] > train_pool["away_score"]).mean())
        flat_draw_rate = float((train_pool["home_score"] == train_pool["away_score"]).mean()) if allows_ties else 0.0
        flat_away_win_rate = 1 - flat_home_win_rate - flat_draw_rate

        dc_fit = None
        if use_dc:
            train_pool_goals = train_pool.rename(columns={"home_score": "home_goals", "away_score": "away_goals"})
            dc_fit = fit_dixon_coles_model(train_pool_goals, dc_teams_universe, as_of_date, half_life_days=DC_HALF_LIFE_DAYS)

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

            row = {
                "date": m["date"].strftime("%Y-%m-%d"), "home_team": home, "away_team": away,
                "actual_home_score": int(m["home_score"]), "actual_away_score": int(m["away_score"]),
                "actual_margin": int(actual_margin), "actual_result": actual,
                "pm_home_win": pm_h, "pm_draw": pm_d, "pm_away_win": pm_a, "pm_mean_margin": mean, "pm_sigma": pm_fit.sigma,
                "elo_home_win": elo_h, "elo_draw": elo_d, "elo_away_win": elo_a,
                "flat_home_win": flat_home_win_rate, "flat_draw": flat_draw_rate, "flat_away_win": flat_away_win_rate,
                "pm_log_loss": log_loss_row(pm_probs, actual), "pm_brier": brier_row(pm_probs, actual), "pm_rps": rps(pm_probs, actual),
                "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                "flat_log_loss": log_loss_row(flat_probs, actual), "flat_brier": brier_row(flat_probs, actual), "flat_rps": rps(flat_probs, actual),
            }

            if pmc_fit is not None:
                rc_home = pmc_fit.elo_run.final_ratings.get(home, 1500.0)
                rc_away = pmc_fit.elo_run.final_ratings.get(away, 1500.0)
                mean_c = pmc_fit.slope * (rc_home - rc_away) + pmc_fit.intercept
                pmc_h, pmc_d, pmc_a = outcome_probabilities(mean_c, pmc_fit.sigma, allows_ties)
                pmc_probs = {"home_win": pmc_h, "draw": pmc_d, "away_win": pmc_a}
                row.update({
                    "pmc_home_win": pmc_h, "pmc_draw": pmc_d, "pmc_away_win": pmc_a,
                    "pmc_log_loss": log_loss_row(pmc_probs, actual), "pmc_brier": brier_row(pmc_probs, actual), "pmc_rps": rps(pmc_probs, actual),
                })

            if use_dc and home in dc_fit.team_index and away in dc_fit.team_index:
                lam, mu = match_lambdas(dc_fit, home, away)
                matrix = score_matrix(lam, mu, dc_fit.rho, max_goals=NHL_MAX_GOALS_GRID)
                dc_h, dc_d, dc_a = dc_outcome_probabilities(matrix)
                dc_probs = {"home_win": dc_h, "draw": dc_d, "away_win": dc_a}
                row.update({
                    "dc_home_win": dc_h, "dc_draw": dc_d, "dc_away_win": dc_a,
                    "dc_log_loss": log_loss_row(dc_probs, actual), "dc_brier": brier_row(dc_probs, actual), "dc_rps": rps(dc_probs, actual),
                })

            rows.append(row)

    match_results = pd.DataFrame(rows)
    out_match_results.parent.mkdir(parents=True, exist_ok=True)
    match_results.to_csv(out_match_results, index=False)
    print(f"Wrote {len(match_results)} real scored backtest games to {out_match_results}")

    candidate_models = ["pm", "elo", "flat"] + (["dc"] if use_dc else []) + (["pmc"] if team_group else [])
    model_names = {
        "pm": "Point-margin model (Elo + margin regression)", "elo": "Elo-only win probability",
        "flat": "Flat/home-field-only baseline", "dc": "Dixon-Coles (real scoreline grid)",
        "pmc": "Point-margin model (conference-aware reversion)",
    }
    comparison_rows = []
    for model in candidate_models:
        # dc's own n_matches can be slightly lower than the other
        # candidates' (a team's very first real appearance in the
        # backtest has no DC fit yet, same real cold-start every Elo-
        # based candidate here also has, just surfaced as a null row
        # instead of a neutral-rating fallback) -- real matches scored,
        # not padded to match the other candidates' count.
        n_scored = int(match_results[f"{model}_log_loss"].notna().sum())
        comparison_rows.append({
            "model": model_names[model],
            "n_matches": n_scored,
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
        dc_note = (
            " A fourth real candidate, Dixon-Coles (src/models/scoreline_models.py, reused as-is), is also "
            "compared here since this sport's real scoring is low/discrete like soccer's, unlike NFL/NBA/NCAA "
            "Football -- not assumed to win, same empirical discipline as every other candidate."
            if use_dc else
            " Soccer's Dixon-Coles/Poisson scoreline grid is NOT a candidate here -- it does not fit this "
            "sport's real scoring scale (confirmed directly, same reasoning as NFL/NBA)."
        )
        if team_group:
            dc_note += (
                " A real conference-aware variant of the point-margin model is also compared (season-reversion "
                "toward each team's own real conference mean -- see elo_model.run_elo's team_group docstring -- "
                "instead of the full real league-wide mean), since this sport's real strength gap between "
                "conferences (e.g. the SEC vs. a Group of 5 conference) is large and persistent -- never "
                "assumed to beat the flat-reversion version."
            )
        f.write(
            f"Real rolling-origin backtest on {len(match_results)} real historical games "
            f"({df['date'].min().date()} to {df['date'].max().date()}, refit every {CHUNK_SIZE} real games using "
            f"only data strictly before that point -- no future leakage). Candidates compared honestly, not "
            f"assumed: the point-margin model (src/models/point_margin_model.py: Elo + a real fitted margin-of-"
            f"victory regression), a plain Elo-only win-probability baseline, and a flat/home-field-only "
            f"baseline.{dc_note}\n\n"
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
    _parser.add_argument("--league", required=True, choices=["nfl", "nba", "nhl", "ncaaf"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
