"""Rolling-origin backtest for a UEFA club competition (UCL, UEL,
UECL), real 2024-25 + 2025-26 data. Generalizes the old, now-removed
backtest_nations_league.py (one competition, one real cycle, no prior
season to warm up on) to three competitions with two real cycles each
-- round 1 of the second real season (2025-26) can be fit on the FULL
first real season (189/189/153 real matches, league phase + knockout),
unlike Nations League's single-cycle case which had nothing to warm up
on at all.

Walks forward through each competition's real LEAGUE-PHASE rounds only
(round_number <= league_phase_rounds, i.e. excluding the knockout
rounds that followed each historical season -- this backtest answers
"how good are our league-phase predictions," the only thing currently
being predicted for 2026-27): refits Dixon-Coles, Elo, and Simple
Poisson before each round using every real match strictly before it
(any stage, both competitions' real history), then scores that round's
league-phase matches. The real knockout matches are NOT scored (out of
scope) but DO feed every model's own continuous rating/fit, same as
any other real result.

Seeded from real domestic-league Elo where one exists (see
cross_competition_elo.py) -- not Nations League's real UEFA-tier seed,
but the same idea: this competition's own 2-season sample is too thin
to estimate 36 teams' relative strength well from nothing, and a club
playing in one of the 5 domestic leagues this project tracks has a far
better-informed real prior than a flat 1500. Leak-free: the seed is
computed from domestic results strictly BEFORE this backtest's own
earliest real match, never "today." Only a partial fix -- a club from
an untracked domestic league (the majority of smaller-league entrants)
still starts flat.

Reuses domestic hyperparameters unchanged from config/model_config.yaml
-- there is nowhere near enough real data here to independently tune
them without overfitting to noise, same discipline as every other
thin-sample competition in this project.

Run: python -m src.evaluation.backtest_continental_cup --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row, rps, team_rolling_goal_avgs  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.baselines import elo_only_probabilities, simple_poisson_baseline  # noqa: E402
from src.models.cross_competition_elo import cross_competition_seed_ratings  # noqa: E402
from src.models.elo_model import run_elo  # noqa: E402
from src.models.scoreline_models import fit_dixon_coles_model, outcome_probabilities, score_matrix  # noqa: E402

MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
with open(MODEL_CONFIG_PATH) as _f:
    _MODEL_CFG = yaml.safe_load(_f)
HALF_LIFE_DAYS = _MODEL_CFG["dixon_coles"]["time_decay_half_life_days"]
L2_REG = _MODEL_CFG["dixon_coles"].get("l2_reg", 0.03)
ELO_K_FACTOR = _MODEL_CFG["elo"]["k_factor"]
ELO_HOME_ADVANTAGE = _MODEL_CFG["elo"]["home_advantage_elo_points"]


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    league_phase_rounds = (cfg.expected_fixture_count or 0) // (cfg.n_teams // 2)
    round_size = cfg.n_teams // 2

    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    out_match_results = REPO_ROOT / "data" / "outputs" / league_path(league_id, "backtest_match_results.csv")
    out_model_comparison = REPO_ROOT / "data" / "outputs" / league_path(league_id, "backtest_model_comparison.csv")
    out_report = REPO_ROOT / "reports" / f"{league_id}_model_selection_report.md"

    df = pd.read_csv(historical_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    teams = sorted(set(df["home_team"]) | set(df["away_team"]))

    # Flat-start Elo (no cross-competition prior) and domestic-seeded Elo
    # (see cross_competition_elo.py) are scored as TWO SEPARATE
    # candidates, not one assumed-better replacement -- the seed only
    # improved UCL's real backtest log loss (0.968 -> 0.946); it made
    # UEL/UECL's slightly WORSE (1.001 -> 1.010, 1.028 -> 1.034), almost
    # certainly because so few of their 36 teams (12 and 4, vs UCL's 21)
    # get a real domestic signal to seed from. Whichever wins each
    # competition's own real backtest is what predict_continental_cup_matches.py
    # and simulate_continental_cup_knockout.py actually use -- see
    # select_elo_variant() below.
    #
    # The seed, when used, is computed from domestic Elo AS OF the
    # EARLIEST real match in this backtest's own historical window, not
    # "today" -- using today's domestic form (which includes 2+ real
    # seasons after this backtest's data ends) to seed a 2024-25
    # continental prediction would be real data leakage and would make
    # this backtest's own reported numbers artificially optimistic. A
    # single static seed at the window's start is leak-free for every
    # round that follows it.
    domestic_seed = cross_competition_seed_ratings(as_of_date=df["date"].min())
    elo_run = run_elo(df, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    elo_pre = elo_run.history[["home_team", "away_team", "date", "home_elo_pre", "away_elo_pre"]]
    elo_seeded_run = run_elo(df, seed_ratings=domestic_seed, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    elo_seeded_pre = elo_seeded_run.history[["home_team", "away_team", "date", "home_elo_pre", "away_elo_pre"]]

    league_phase = df[df["stage"] == "league_phase"].reset_index(drop=True)
    # (season, round_number) pairs in chronological order, league-phase only.
    round_keys = sorted(league_phase[["season", "round_number"]].drop_duplicates().itertuples(index=False, name=None))

    rows = []
    for season, round_number in round_keys:
        round_matches = league_phase[(league_phase["season"] == season) & (league_phase["round_number"] == round_number)]
        as_of_date = round_matches["date"].min()
        history_before = df[df["date"] < as_of_date]
        if history_before.empty or round_matches.empty:
            continue  # the very first round overall has no real prior data to fit on

        dc_fit = fit_dixon_coles_model(history_before, teams, as_of_date, half_life_days=HALF_LIFE_DAYS, l2_reg=L2_REG)
        league_avg_goals = float(pd.concat([history_before["home_goals"], history_before["away_goals"]]).mean())

        for _, m in round_matches.iterrows():
            home, away = m["home_team"], m["away_team"]
            actual = m["result"]

            lam = float(np.exp(dc_fit.home_advantage + dc_fit.attack[dc_fit.team_index[home]] - dc_fit.defense[dc_fit.team_index[away]]))
            mu = float(np.exp(dc_fit.attack[dc_fit.team_index[away]] - dc_fit.defense[dc_fit.team_index[home]]))
            matrix = score_matrix(lam, mu, dc_fit.rho)
            dc_h, dc_d, dc_a = outcome_probabilities(matrix)

            elo_row = elo_pre[(elo_pre["home_team"] == home) & (elo_pre["away_team"] == away) & (elo_pre["date"] == m["date"])]
            r_home, r_away = float(elo_row["home_elo_pre"].iloc[0]), float(elo_row["away_elo_pre"].iloc[0])
            elo_h, elo_d, elo_a = elo_only_probabilities(r_home, r_away, ELO_HOME_ADVANTAGE)

            elo_seeded_row = elo_seeded_pre[(elo_seeded_pre["home_team"] == home) & (elo_seeded_pre["away_team"] == away) & (elo_seeded_pre["date"] == m["date"])]
            rs_home, rs_away = float(elo_seeded_row["home_elo_pre"].iloc[0]), float(elo_seeded_row["away_elo_pre"].iloc[0])
            eloseeded_h, eloseeded_d, eloseeded_a = elo_only_probabilities(rs_home, rs_away, ELO_HOME_ADVANTAGE)

            h_gf, h_ga = team_rolling_goal_avgs(history_before, home)
            a_gf, a_ga = team_rolling_goal_avgs(history_before, away)
            sp_lam, sp_mu = simple_poisson_baseline(h_gf, h_ga, a_gf, a_ga, league_avg_goals)
            sp_matrix = score_matrix(sp_lam, sp_mu, rho=0.0)
            sp_h, sp_d, sp_a = outcome_probabilities(sp_matrix)

            dc_probs = {"home_win": dc_h, "draw": dc_d, "away_win": dc_a}
            elo_probs = {"home_win": elo_h, "draw": elo_d, "away_win": elo_a}
            eloseeded_probs = {"home_win": eloseeded_h, "draw": eloseeded_d, "away_win": eloseeded_a}
            sp_probs = {"home_win": sp_h, "draw": sp_d, "away_win": sp_a}

            rows.append({
                "season": season, "round_number": round_number, "date": m["date"].strftime("%Y-%m-%d"),
                "home_team": home, "away_team": away,
                "actual_home_goals": int(m["home_goals"]), "actual_away_goals": int(m["away_goals"]), "actual_result": actual,
                "dc_home_win": dc_h, "dc_draw": dc_d, "dc_away_win": dc_a,
                "dc_lambda": lam, "dc_mu": mu, "dc_rho": dc_fit.rho,
                "elo_home_win": elo_h, "elo_draw": elo_d, "elo_away_win": elo_a,
                "eloseeded_home_win": eloseeded_h, "eloseeded_draw": eloseeded_d, "eloseeded_away_win": eloseeded_a,
                "simplepoisson_home_win": sp_h, "simplepoisson_draw": sp_d, "simplepoisson_away_win": sp_a,
                "dc_log_loss": log_loss_row(dc_probs, actual), "dc_brier": brier_row(dc_probs, actual), "dc_rps": rps(dc_probs, actual),
                "elo_log_loss": log_loss_row(elo_probs, actual), "elo_brier": brier_row(elo_probs, actual), "elo_rps": rps(elo_probs, actual),
                "eloseeded_log_loss": log_loss_row(eloseeded_probs, actual), "eloseeded_brier": brier_row(eloseeded_probs, actual),
                "eloseeded_rps": rps(eloseeded_probs, actual),
                "simplepoisson_log_loss": log_loss_row(sp_probs, actual), "simplepoisson_brier": brier_row(sp_probs, actual),
                "simplepoisson_rps": rps(sp_probs, actual),
            })

    match_results = pd.DataFrame(rows)
    out_match_results.parent.mkdir(parents=True, exist_ok=True)
    match_results.to_csv(out_match_results, index=False)
    print(f"Wrote {len(match_results)} real scored backtest matches to {out_match_results}")

    comparison_rows = []
    for model in ["dc", "elo", "eloseeded", "simplepoisson"]:
        comparison_rows.append({
            "model": {
                "dc": "Dixon-Coles (main model)", "elo": "Elo-only, flat start",
                "eloseeded": "Elo-only, domestic-Elo-seeded", "simplepoisson": "Simple Poisson baseline",
            }[model],
            "n_matches": len(match_results),
            "log_loss": match_results[f"{model}_log_loss"].mean(),
            "brier_score": match_results[f"{model}_brier"].mean(),
            "ranked_probability_score": match_results[f"{model}_rps"].mean(),
        })
    comparison = pd.DataFrame(comparison_rows).sort_values("log_loss")
    comparison.to_csv(out_model_comparison, index=False)
    print(f"Wrote model comparison to {out_model_comparison}")

    best = comparison.iloc[0]
    n_seeded = sum(1 for t in teams if t in domestic_seed)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w") as f:
        f.write(f"# {cfg.display_name} Model Selection Report\n\n")
        f.write(
            f"**Genuinely thin backtest -- read with real caution.** {cfg.display_name} has only two real "
            f"cycles (2024-25, 2025-26) to validate on under the current 36-team Swiss-model league phase -- "
            f"versus 2,000+ real matches for each domestic league in this project. This backtest scores "
            f"{len(match_results)} real LEAGUE-PHASE matches (every league-phase round after the very first, "
            f"which has no real prior data to fit on); real knockout-round results from both historical "
            f"cycles feed every model's fit but are not themselves scored (knockout-stage prediction is a "
            f"separate, not-yet-built capability). Dixon-Coles/Elo/Simple-Poisson hyperparameters are reused "
            f"unchanged from the domestic config (config/model_config.yaml); there is not enough real data "
            f"here to independently tune them without overfitting to noise.\n\n"
        )
        f.write("## Model comparison (lower log loss / Brier / RPS is better)\n\n")
        f.write(comparison.to_markdown(index=False))
        f.write(f"\n\n## Selected model\n\n**{best['model']}** has the lowest backtest log loss "
                f"({best['log_loss']:.4f}) and is used as the primary model for 2026-27 league-phase "
                f"predictions.\n\n")
        f.write(
            "## Cross-competition Elo seed (src/models/cross_competition_elo.py)\n\n"
            f"{n_seeded} of this backtest's {len(teams)} real historical-window teams have a real domestic "
            f"Elo rating (EPL/La Liga/Serie A/Bundesliga/Ligue 1) to seed from; the rest start flat at 1500, "
            "same as before this existed. Scored as its own candidate (\"Elo-only, domestic-Elo-seeded\") "
            "above, not assumed better: the real backtest result is what decides whether this competition's "
            f"predictions actually use it -- {'it won here' if best['model'] == 'Elo-only, domestic-Elo-seeded' else 'it did NOT win here, so predictions use the flat-start Elo instead'}.\n\n"
        )
        f.write(
            "## Limitations\n\n"
            "- Sample size (see above) is far too small for isotonic calibration (this project's own "
            "500-match minimum) -- raw model probabilities are used uncalibrated.\n"
            "- No historical market-odds source exists for this competition (no football-data.co.uk "
            "coverage) -- no model+market blend backtest could be run; real current market odds (The "
            "Odds API) are shown alongside predictions for comparison only, not blended in.\n"
            f"- Time-decay half-life ({HALF_LIFE_DAYS:.0f} days) and all other hyperparameters are the "
            "domestic, club-football-tuned defaults, not independently validated for this competition's "
            "much sparser real match calendar.\n"
            "- The domestic-Elo seed only covers a club playing in one of the 5 domestic leagues this "
            "project tracks -- the majority of smaller-league entrants (and every non-European-covered "
            "country) get no real cross-competition signal at all.\n"
        )
    print(f"Wrote model selection report to {out_report}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
