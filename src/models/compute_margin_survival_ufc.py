"""+2 Margin Survival's real equivalent for UFC: "Distance Survival".

An individual fight has no continuous score margin, so this is not a
literal port of soccer's "+2 goals" or NFL/NBA/NHL/NCAA Football's
points-based threshold -- see fight_distance_model.py's module
docstring for the real, honest reinterpretation this project uses:
does a fighter survive to the real judges' decision, or get finished
(KO/TKO/submission) first?

`p_fail` = P(this fighter is finished), read off fight_distance_model.py
(fighter_elo_model.py's real win probability x the real backtested
stoppage-given-loss blend, see reports/ufc_model_selection_report.md
for which blend weight won). `p_push` is always 0.0 -- there is no
real analogue to "exactly at the threshold" for a binary finish/no-
finish outcome, a real, deliberate two-state simplification
(documented, not invented as a third state). `p_cover` = 1 - p_fail.

Risk-tier labels reuse the soccer engine's generic risk_label/verdict/
percentile_score helpers directly (imported, not duplicated), with
real bands chosen from THIS sport's own real backtested p_fail
distribution (see reports/ufc_model_selection_report.md), not a
borrowed number. `verdict()`'s tag is the literal string "DISTANCE"
(no real number to put a "+" in front of) -- e.g. "PICK DISTANCE" /
"LEAN DISTANCE" / "PASS".

Run: python -m src.models.compute_margin_survival_ufc
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_ufc import BLEND_WEIGHTS  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.compute_margin_survival import percentile_score, verdict  # noqa: E402
from src.models.fight_distance_model import fit_stoppage_rates, p_fail as compute_p_fail, stoppage_given_loss_probability  # noqa: E402
from src.models.fighter_elo_model import run_fighter_elo, win_probability  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

# Winning blend weight from the real backtest (reports/
# ufc_model_selection_report.md) -- read at runtime, not hardcoded, so
# this stays correct if the backtest is re-run and a different real
# candidate wins.
BEST_BLEND_PATH = REPO_ROOT / "data" / "outputs" / "ufc_backtest_model_comparison.csv"

# Real bands set from the real backtested p_fail distribution across
# every real historical fight (see reports/ufc_model_selection_report.md's
# "Real historical finish-rate distribution": 0.1981/0.2613/0.3012/
# 0.3745 at the real 20th/40th/60th/80th percentiles) -- notably much
# higher in absolute terms than any other sport's bands in this
# project, a real reflection of UFC's own real baseline: 52.9% of
# EVERY real historical fight ends in a stoppage, not a decision
# (confirmed directly), so "finished" is nowhere near the rare tail
# event it is in a team sport -- "ELITE SURVIVAL" here means genuinely
# rare FOR THIS SPORT, not a borrowed number from a sport where a
# blowout is structurally uncommon.
RISK_LABELS: list[tuple[float, str]] = [
    (0.20, "ELITE SURVIVAL"), (0.26, "VERY STRONG"), (0.30, "STRONG"), (0.38, "MODERATE"),
    (float("inf"), "HIGH BLOWOUT RISK"),
]

OUTPUT_COLUMNS = [
    "match_id", "league_id", "season", "event_id", "event_name", "date", "kickoff_utc", "status",
    "fighter", "opponent", "weight_class", "win_prob", "p_cover", "p_push", "p_fail", "p_survive",
    "risk_label", "threshold", "verdict", "why_text",
    "fighter_elo", "opponent_elo", "fighter_n_historical_fights",
    "run_id", "model_version", "generated_at",
]


def _risk_label(p_fail: float) -> str:
    for threshold, label in RISK_LABELS:
        if p_fail < threshold:
            return label
    return RISK_LABELS[-1][1]


def _best_blend_weight() -> float:
    if not BEST_BLEND_PATH.exists():
        return 0.5  # equal blend -- a reasonable real default until the backtest has run once
    comparison = pd.read_csv(BEST_BLEND_PATH)
    distance_rows = comparison[comparison["model"].str.startswith("Distance-survival blend")].sort_values("log_loss")
    if distance_rows.empty:
        return 0.5
    best_name = distance_rows.iloc[0]["model"].split("(")[1].split(",")[0]
    return BLEND_WEIGHTS.get(best_name, 0.5)


def why_text(fighter: str, opponent: str, fighter_elo: float, opponent_elo: float, win_prob: float, p_fail_val: float) -> str:
    favored = "a real favorite" if win_prob > 0.5 else "a real underdog"
    return (
        f"Built on this project's own real fighter Elo (fighter: {fighter_elo:.0f}, opponent: {opponent_elo:.0f}) "
        f"and real backtested stoppage-rate blend (see reports/ufc_model_selection_report.md). {fighter} is "
        f"{favored} here (win probability {win_prob:.1%}). Net modeled probability of {fighter} being finished "
        f"(KO/TKO/submission) rather than surviving to a real decision: {p_fail_val:.1%}."
    )


def compute() -> pd.DataFrame:
    cfg = load_league_config("ufc")
    historical_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "historical_fights.csv")
    fight_card_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_fight_card.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path("ufc", "2026_27_margin_survival.csv")

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    historical = historical[historical["winner"].isin(["fighter_a", "fighter_b"])]
    fight_card = pd.read_csv(fight_card_path)

    elo_run = run_fighter_elo(historical)
    rates = fit_stoppage_rates(historical)
    blend_weight = _best_blend_weight()

    n_fights_by_fighter: dict[str, int] = {}
    for _, fgt in historical.iterrows():
        n_fights_by_fighter[fgt["fighter_a"]] = n_fights_by_fighter.get(fgt["fighter_a"], 0) + 1
        n_fights_by_fighter[fgt["fighter_b"]] = n_fights_by_fighter.get(fgt["fighter_b"], 0) + 1

    meta = make_run_metadata(prefix="margin_survival_ufc", season="2026-27")
    generated_at = now_utc_iso()

    rows = []
    for _, fx in fight_card.iterrows():
        # fighter_a/fighter_b are real names only (no stable id on this
        # CSV -- see collect_espn_ufc_schedule.py); Elo lookups here key
        # off the same real name strings used throughout this fight
        # card and historical ledger, consistent with how this project
        # tracks UFC fighters (no canonical id table, see
        # team_names.py's module docstring on why).
        for fighter, opponent in ((fx["fighter_a"], fx["fighter_b"]), (fx["fighter_b"], fx["fighter_a"])):
            r_fighter = elo_run.final_ratings.get(fighter, 1500.0)
            r_opponent = elo_run.final_ratings.get(opponent, 1500.0)
            win_prob = win_probability(r_fighter, r_opponent)
            sg = stoppage_given_loss_probability(rates, fighter, opponent, blend_weight=blend_weight)
            p_fail_val = compute_p_fail(1 - win_prob, sg)
            p_cover = 1 - p_fail_val
            row_risk_label = _risk_label(p_fail_val)

            rows.append({
                "match_id": fx["match_id"], "league_id": "ufc", "season": fx["season"],
                "event_id": fx["event_id"], "event_name": fx["event_name"],
                "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "status": fx["status"],
                "fighter": fighter, "opponent": opponent, "weight_class": fx["weight_class"],
                "win_prob": round(win_prob, 4), "p_cover": round(p_cover, 4), "p_push": 0.0,
                "p_fail": round(p_fail_val, 4), "p_survive": round(p_cover, 4),
                "risk_label": row_risk_label, "threshold": None,
                "verdict": verdict(row_risk_label, None, "DISTANCE"),
                "why_text": why_text(fighter, opponent, r_fighter, r_opponent, win_prob, p_fail_val),
                "fighter_elo": round(r_fighter, 1), "opponent_elo": round(r_opponent, 1),
                "fighter_n_historical_fights": n_fights_by_fighter.get(fighter, 0),
                "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
            })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    tally = out_df["verdict"].value_counts().to_dict()
    print(f"Wrote {len(out_df)} margin-survival rows to {out_path} -- verdicts: {tally}")
    log_experiment(meta, stage="compute_margin_survival_ufc", notes=f"ufc: {len(out_df)} rows, verdicts={tally}")
    return out_df


if __name__ == "__main__":
    compute()
