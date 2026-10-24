"""Rolling-origin backtest for UFC, real historical data (see
collect_espn_ufc_historical.py -- several real past calendar years).

Two real models backtested, both walking forward through every real
historical fight in chronological order, refitting every CHUNK_SIZE
real fights using only real data strictly before that point (same
no-leakage discipline as backtest_team_sport.py):

1. **Win model** (fighter_elo_model.py) vs. a flat 50/50 baseline --
   does the real Elo rating actually beat a coin flip?
2. **Distance-survival model** (fight_distance_model.py): three real
   candidate blend weights for `stoppage_given_loss_probability`
   (fighter's own real vulnerability rate only, opponent's own real
   finishing rate only, and an equal real blend of both) are compared
   on real log loss/Brier predicting whether the ACTUAL loser in each
   real fight was finished -- never assumed, the real backtest picks
   the winner.

Also reports the real historical "finish rate" distribution (what
real fraction of fights end in a stoppage vs. a decision, and each
real fighter's own real p_fail distribution across their real
historical fights) -- the basis for Distance Survival's real risk-tier
bands (see compute_margin_survival_ufc.py), same discipline as every
other sport's thresholds in this project.

Run: python -m src.evaluation.backtest_ufc
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row  # noqa: E402
from src.leagues import league_path  # noqa: E402
from src.models.fight_distance_model import fit_stoppage_rates, p_fail as compute_p_fail, stoppage_given_loss_probability  # noqa: E402
from src.models.fighter_elo_model import run_fighter_elo, win_probability  # noqa: E402

CHUNK_SIZE = 30
MIN_TRAIN_FIGHTS = 50
BLEND_WEIGHTS = {"fighter_only": 1.0, "opponent_only": 0.0, "equal_blend": 0.5}


def main() -> None:
    historical_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "historical_fights.csv")
    out_match_results = REPO_ROOT / "data" / "outputs" / "ufc_backtest_match_results.csv"
    out_model_comparison = REPO_ROOT / "data" / "outputs" / "ufc_backtest_model_comparison.csv"
    out_report = REPO_ROOT / "reports" / "ufc_model_selection_report.md"

    df = pd.read_csv(historical_path, parse_dates=["date"])
    df = df[df["winner"].isin(["fighter_a", "fighter_b"])].sort_values("date").reset_index(drop=True)

    rows = []
    n_chunks = int(np.ceil(len(df) / CHUNK_SIZE))
    for c in range(n_chunks):
        chunk = df.iloc[c * CHUNK_SIZE:(c + 1) * CHUNK_SIZE]
        if chunk.empty:
            continue
        as_of_date = chunk["date"].iloc[0]
        train_pool = df[df["date"] < as_of_date]
        if len(train_pool) < MIN_TRAIN_FIGHTS:
            continue

        elo_run = run_fighter_elo(train_pool)
        rates = fit_stoppage_rates(train_pool)

        for _, fgt in chunk.iterrows():
            a, b = fgt["fighter_a"], fgt["fighter_b"]
            r_a = elo_run.final_ratings.get(a, 1500.0)
            r_b = elo_run.final_ratings.get(b, 1500.0)
            win_prob_a = win_probability(r_a, r_b)
            actual_a_won = 1 if fgt["winner"] == "fighter_a" else 0

            row = {
                "date": fgt["date"].strftime("%Y-%m-%d"), "fighter_a": a, "fighter_b": b,
                "win_prob_a": win_prob_a, "actual_a_won": actual_a_won,
                "elo_log_loss": log_loss_row({"home_win": win_prob_a, "draw": 0.0, "away_win": 1 - win_prob_a}, "home_win" if actual_a_won else "away_win"),
                "elo_brier": brier_row({"home_win": win_prob_a, "draw": 0.0, "away_win": 1 - win_prob_a}, "home_win" if actual_a_won else "away_win"),
                "flat_log_loss": log_loss_row({"home_win": 0.5, "draw": 0.0, "away_win": 0.5}, "home_win" if actual_a_won else "away_win"),
                "flat_brier": brier_row({"home_win": 0.5, "draw": 0.0, "away_win": 0.5}, "home_win" if actual_a_won else "away_win"),
            }

            # Real distance-survival target: did the ACTUAL loser of
            # this real fight get finished? Scored against each real
            # candidate blend weight for whichever fighter actually lost.
            loser_id, winner_id = (b, a) if actual_a_won else (a, b)
            actual_stoppage = 1 if fgt["method"] == "finish" else 0
            for name, weight in BLEND_WEIGHTS.items():
                predicted = stoppage_given_loss_probability(rates, loser_id, winner_id, blend_weight=weight)
                row[f"{name}_log_loss"] = log_loss_row({"home_win": predicted, "draw": 0.0, "away_win": 1 - predicted}, "home_win" if actual_stoppage else "away_win")
                row[f"{name}_brier"] = brier_row({"home_win": predicted, "draw": 0.0, "away_win": 1 - predicted}, "home_win" if actual_stoppage else "away_win")

            rows.append(row)

    match_results = pd.DataFrame(rows)
    out_match_results.parent.mkdir(parents=True, exist_ok=True)
    match_results.to_csv(out_match_results, index=False)
    print(f"Wrote {len(match_results)} real scored backtest fights to {out_match_results}")

    win_comparison = pd.DataFrame([
        {"model": "Fighter Elo (win model)", "n_fights": len(match_results), "log_loss": match_results["elo_log_loss"].mean(), "brier_score": match_results["elo_brier"].mean()},
        {"model": "Flat 50/50 baseline", "n_fights": len(match_results), "log_loss": match_results["flat_log_loss"].mean(), "brier_score": match_results["flat_brier"].mean()},
    ]).sort_values("log_loss")

    distance_comparison = pd.DataFrame([
        {"model": f"Distance-survival blend ({name}, weight={weight})", "n_fights": len(match_results),
         "log_loss": match_results[f"{name}_log_loss"].mean(), "brier_score": match_results[f"{name}_brier"].mean()}
        for name, weight in BLEND_WEIGHTS.items()
    ]).sort_values("log_loss")
    best_blend_name = distance_comparison.iloc[0]["model"].split("(")[1].split(",")[0]

    comparison = pd.concat([win_comparison, distance_comparison], ignore_index=True)
    comparison.to_csv(out_model_comparison, index=False)
    print(f"Wrote model comparison to {out_model_comparison}")

    # Real historical finish-rate distribution -- the basis for
    # Distance Survival's real risk-tier bands.
    overall_finish_rate = float((df["method"] == "finish").mean())
    rates_full = fit_stoppage_rates(df)
    all_p_fail = []
    elo_full = run_fighter_elo(df)
    for _, fgt in df.iterrows():
        loser_id, winner_id = (fgt["fighter_b"], fgt["fighter_a"]) if fgt["winner"] == "fighter_a" else (fgt["fighter_a"], fgt["fighter_b"])
        r_winner = elo_full.final_ratings.get(winner_id, 1500.0)
        r_loser = elo_full.final_ratings.get(loser_id, 1500.0)
        win_prob_winner = win_probability(r_winner, r_loser)
        sg = stoppage_given_loss_probability(rates_full, loser_id, winner_id, blend_weight=BLEND_WEIGHTS.get(best_blend_name.strip(), 0.5))
        all_p_fail.append(compute_p_fail(win_prob_winner, sg))
    p_fail_percentiles = {p: float(np.percentile(all_p_fail, p)) for p in [20, 40, 60, 80]}

    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w") as f:
        f.write("# UFC Model Selection Report\n\n")
        f.write(
            f"Real rolling-origin backtest on {len(match_results)} real historical fights "
            f"({df['date'].min().date()} to {df['date'].max().date()}, refit every {CHUNK_SIZE} real fights using "
            "only data strictly before that point -- no future leakage). UFC has no continuous score margin, so "
            "two SEPARATE real models are backtested: a win-probability model (src/models/fighter_elo_model.py, "
            "a plain win/loss Elo -- not soccer's/NFL's margin-of-victory-weighted Elo, which has no real analogue "
            "for an individual fight), and a Distance Survival model (src/models/fight_distance_model.py) "
            "predicting whether a fight ends in a real stoppage -- this project's real equivalent of +2 Margin "
            "Survival for this sport.\n\n"
        )
        f.write("## Win model comparison (lower log loss / Brier is better)\n\n")
        f.write(win_comparison.to_markdown(index=False))
        f.write("\n\n## Distance-survival blend-weight comparison\n\n")
        f.write(distance_comparison.to_markdown(index=False))
        f.write(f"\n\nSelected blend: **{best_blend_name.strip()}** (lowest real backtest log loss) -- used by "
                "compute_margin_survival_ufc.py for every real upcoming fight.\n\n")
        f.write("## Real historical finish-rate distribution\n\n")
        f.write(f"Overall real share of fights ending in a stoppage (not a decision): **{overall_finish_rate:.1%}** "
                f"across {len(df)} real historical fights.\n\n")
        f.write("Real per-fighter `p_fail` distribution (every real historical fight, both fighters' perspective), "
                "the basis for Distance Survival's real risk-tier bands:\n\n")
        f.write("| Percentile | p_fail |\n|---|---|\n")
        for p, v in p_fail_percentiles.items():
            f.write(f"| {p}th | {v:.4f} |\n")
        f.write(
            "\nUsed directly by compute_margin_survival_ufc.py to set Distance Survival's real risk-tier bands -- "
            "see that module's docstring for the exact choice.\n\n"
        )
        f.write(
            "## Limitations\n\n"
            "- No real market-odds blending (UFC's h2h-only real market, see collect_odds.py, is shown for "
            "comparison only, same as every other league's model-only predictions where blending isn't yet wired "
            "in).\n"
            "- One real global Elo rating per fighter, not per weight class -- a fighter who changes weight class "
            "keeps their one real rating (see fighter_elo_model.py's module docstring).\n"
            "- `stoppage_given_loss_probability`'s blend weight is chosen from three real candidates (fighter-only, "
            "opponent-only, equal blend) -- a continuously-fit logistic blend is a real, separate possible "
            "refinement, not attempted here.\n"
        )
    print(f"Wrote model selection report to {out_report}")


if __name__ == "__main__":
    main()
