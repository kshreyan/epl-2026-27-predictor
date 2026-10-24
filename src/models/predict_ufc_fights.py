"""Real upcoming UFC fight-card predictions.

Win probability comes from fighter_elo_model.py's real fighter Elo
(see reports/ufc_model_selection_report.md for the real backtest that
validated it beats a flat 50/50 baseline). There is no real continuous
score to predict -- no `predicted_score_model_only` concept exists for
an individual fight (unlike every team sport in this project), so this
module instead predicts the real most-likely OUTCOME shape:
`predicted_outcome` is "Decision" if P(decision) is the single most
likely real category, or "Finish" otherwise, paired with
`predicted_distance_survival` (this fight's own real P(goes the
distance), from fight_distance_model.py, averaged across both
fighters' own real stoppage risk).

Market: UFC has a real h2h (moneyline) market only (confirmed directly
-- no real spread/totals market exists for an individual fight, see
collect_odds.py), so `market_blend_applied` never applies here; real
market odds are shown for comparison only, same as every other
league's model-only predictions before blending is validated.

Run: python -m src.models.predict_ufc_fights
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.fight_distance_model import fit_stoppage_rates, p_fail as compute_p_fail, stoppage_given_loss_probability  # noqa: E402
from src.models.fighter_elo_model import run_fighter_elo, win_probability  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

DATA_QUALITY_SCORE = 0.3  # several real years of real data -- consistent with the other American-sport leagues

OUTPUT_COLUMNS = [
    "match_id", "season", "event_id", "event_name", "date", "kickoff_utc", "status",
    "fighter_a", "fighter_b", "weight_class", "scheduled_rounds",
    "actual_winner", "actual_method", "actual_finish_round",
    "fighter_a_win_prob", "fighter_b_win_prob", "moneyline_pick",
    "predicted_outcome", "fighter_a_distance_survival_prob", "fighter_b_distance_survival_prob",
    "fighter_a_elo", "fighter_b_elo", "confidence", "upset_risk", "data_quality_score",
    "market_available", "market_fighter_a_odds", "market_fighter_b_odds",
    "injury_data_available", "lineup_data_available",
    "run_id", "model_version", "generated_at",
]


def load_market_odds(odds_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not odds_path.exists():
        return out
    with open(odds_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["market_type"] != "h2h" or row["is_real_data"] != "True":
                continue
            mid = row["match_id"]
            if mid in out or not row["current_home_odds"] or not row["current_away_odds"]:
                continue
            out[mid] = {"fighter_a": float(row["current_home_odds"]), "fighter_b": float(row["current_away_odds"])}
    return out


def load_real_results(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["match_id"]] = row
    return out


def main() -> None:
    cfg = load_league_config("ufc")
    historical_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "historical_fights.csv")
    fight_card_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_fight_card.csv")
    odds_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_real_odds.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path("ufc", "2026_27_match_predictions.csv")

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    historical = historical[historical["winner"].isin(["fighter_a", "fighter_b"])]
    fight_card = pd.read_csv(fight_card_path)
    market_odds = load_market_odds(odds_path)
    real_results = load_real_results(real_results_path)

    elo_run = run_fighter_elo(historical)
    rates = fit_stoppage_rates(historical)
    blend_weight = 0.5  # real backtested winner -- see reports/ufc_model_selection_report.md

    meta = make_run_metadata(prefix="predict_ufc", season="2026-27")
    generated_at = now_utc_iso()

    rows = []
    n_with_market = 0
    for _, fx in fight_card.iterrows():
        r_a = elo_run.final_ratings.get(fx["fighter_a"], 1500.0)
        r_b = elo_run.final_ratings.get(fx["fighter_b"], 1500.0)
        win_prob_a = win_probability(r_a, r_b)
        win_prob_b = 1 - win_prob_a

        sg_a = stoppage_given_loss_probability(rates, fx["fighter_a"], fx["fighter_b"], blend_weight=blend_weight)
        sg_b = stoppage_given_loss_probability(rates, fx["fighter_b"], fx["fighter_a"], blend_weight=blend_weight)
        p_fail_a = compute_p_fail(win_prob_b, sg_a)
        p_fail_b = compute_p_fail(win_prob_a, sg_b)
        distance_survival_a, distance_survival_b = 1 - p_fail_a, 1 - p_fail_b

        overall_finish_prob = win_prob_a * sg_a + win_prob_b * sg_b
        predicted_outcome = "Finish" if overall_finish_prob > 0.5 else "Decision"
        moneyline_pick = fx["fighter_a"] if win_prob_a > win_prob_b else fx["fighter_b"]
        confidence = round(max(win_prob_a, win_prob_b), 4)
        upset_risk = round(min(win_prob_a, win_prob_b), 4)

        odds = market_odds.get(fx["match_id"])
        market_available = odds is not None
        if market_available:
            n_with_market += 1

        result = real_results.get(fx["match_id"])

        rows.append({
            "match_id": fx["match_id"], "season": fx["season"], "event_id": fx["event_id"], "event_name": fx["event_name"],
            "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "status": fx["status"],
            "fighter_a": fx["fighter_a"], "fighter_b": fx["fighter_b"],
            "weight_class": fx["weight_class"], "scheduled_rounds": fx["scheduled_rounds"],
            "actual_winner": (fx["fighter_a"] if result and result["winner"] == "fighter_a" else fx["fighter_b"]) if result else "",
            "actual_method": result["method"] if result else "",
            "actual_finish_round": result["finish_round"] if result else "",
            "fighter_a_win_prob": round(win_prob_a, 4), "fighter_b_win_prob": round(win_prob_b, 4),
            "moneyline_pick": moneyline_pick, "predicted_outcome": predicted_outcome,
            "fighter_a_distance_survival_prob": round(distance_survival_a, 4),
            "fighter_b_distance_survival_prob": round(distance_survival_b, 4),
            "fighter_a_elo": round(r_a, 1), "fighter_b_elo": round(r_b, 1),
            "confidence": confidence, "upset_risk": upset_risk, "data_quality_score": DATA_QUALITY_SCORE,
            "market_available": market_available,
            "market_fighter_a_odds": odds["fighter_a"] if odds else None,
            "market_fighter_b_odds": odds["fighter_b"] if odds else None,
            "injury_data_available": False, "lineup_data_available": False,
            "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} predictions to {out_path} ({n_with_market} with real current market odds)")
    log_experiment(meta, stage="predict_ufc_fights", notes=f"{len(out_df)} fights, {n_with_market} with real market odds")


if __name__ == "__main__":
    main()
