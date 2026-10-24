"""Real, model-derived UFC fighter power rankings per weight class.

**Not a claim to reproduce the real official UFC rankings panel** --
that's voted on by a real media panel, not a formula, same reasoning
this project uses for not fabricating a substitute for NCAA Football's
real committee-selected playoff. This is this project's own real,
backtested Elo rating (fighter_elo_model.py, validated against a flat
baseline -- see reports/ufc_model_selection_report.md), labeled
plainly as model output throughout the frontend.

Ranked within each fighter's own most recent real weight class (see
fighter_elo_model.py's module docstring on why the rating itself is
one real global number, not split per class) -- grouped for display
only. Only fighters with at least MIN_RANKED_FIGHTS real fights in the
last RECENT_YEARS real years are ranked -- an inactive or debut
fighter's real Elo is too thin/stale to rank meaningfully, the same
"too thin to compute reliably" discipline used elsewhere in this
project (e.g. fight_distance_model.py's MIN_FIGHTS).

Run: python -m src.models.rank_ufc_fighters
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import league_path  # noqa: E402
from src.models.fighter_elo_model import run_fighter_elo  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

MIN_RANKED_FIGHTS = 3
RECENT_YEARS = 3
TOP_N_PER_CLASS = 15

OUTPUT_COLUMNS = ["weight_class", "rank", "fighter", "elo", "n_real_fights_total", "last_real_fight_date", "generated_at", "model_version"]


def main() -> None:
    historical_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "historical_fights.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path("ufc", "fighter_rankings.csv")

    df = pd.read_csv(historical_path, parse_dates=["date"])
    df = df[df["winner"].isin(["fighter_a", "fighter_b"])]

    elo_run = run_fighter_elo(df)

    n_fights: dict[str, int] = {}
    last_fight: dict[str, pd.Timestamp] = {}
    for _, fgt in df.iterrows():
        for fighter in (fgt["fighter_a"], fgt["fighter_b"]):
            n_fights[fighter] = n_fights.get(fighter, 0) + 1
            if fighter not in last_fight or fgt["date"] > last_fight[fighter]:
                last_fight[fighter] = fgt["date"]

    recent_cutoff = pd.Timestamp(datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365 * RECENT_YEARS))
    rows = []
    for fighter, elo in elo_run.final_ratings.items():
        if n_fights.get(fighter, 0) < MIN_RANKED_FIGHTS:
            continue
        if last_fight.get(fighter, pd.Timestamp.min) < recent_cutoff:
            continue
        rows.append({
            "weight_class": elo_run.last_weight_class.get(fighter, ""),
            "fighter": fighter, "elo": round(elo, 1),
            "n_real_fights_total": n_fights.get(fighter, 0),
            "last_real_fight_date": last_fight[fighter].strftime("%Y-%m-%d"),
        })

    generated_at = now_utc_iso()
    out_rows = []
    for _, group in pd.DataFrame(rows).groupby("weight_class"):
        ranked = group.sort_values("elo", ascending=False).head(TOP_N_PER_CLASS).reset_index(drop=True)
        for i, r in ranked.iterrows():
            out_rows.append({
                "weight_class": r["weight_class"], "rank": i + 1, "fighter": r["fighter"], "elo": r["elo"],
                "n_real_fights_total": r["n_real_fights_total"], "last_real_fight_date": r["last_real_fight_date"],
                "generated_at": generated_at, "model_version": MODEL_VERSION,
            })

    out_df = pd.DataFrame(out_rows)[OUTPUT_COLUMNS] if out_rows else pd.DataFrame(columns=OUTPUT_COLUMNS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} ranked fighters across {out_df['weight_class'].nunique()} weight classes to {out_path}")


if __name__ == "__main__":
    main()
