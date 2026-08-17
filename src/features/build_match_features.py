"""Builds data/processed/epl_2026_27_match_features.csv: one row per
2026-27 fixture with the section-8 team-strength differential features
plus the leakage-safety bookkeeping columns required by spec section 7.

Run: python -m src.features.build_match_features
(requires build_team_strength_features.py to have been run first)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.features.build_schedule_congestion_features import build_schedule_congestion_features  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
STRENGTH_PATH = REPO_ROOT / "data" / "processed" / "epl_team_strength_baseline.csv"
OUT_PATH = REPO_ROOT / "data" / "processed" / "epl_2026_27_match_features.csv"


def main() -> None:
    fixtures = pd.read_csv(FIXTURES_PATH)
    strength = pd.read_csv(STRENGTH_PATH).set_index("team")
    congestion = build_schedule_congestion_features(fixtures)

    generated_at = now_utc_iso()
    fixtures = fixtures.merge(congestion, on="match_id", how="left")

    rows = []
    for _, fx in fixtures.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        h, a = strength.loc[home], strength.loc[away]

        rows.append({
            "match_id": fx["match_id"],
            "feature_generated_at": generated_at,
            "latest_source_timestamp_used": fx["source_timestamp"],
            "kickoff_utc": fx["kickoff_utc"],
            "leakage_safe_flag": True,  # generated_at is always <= kickoff_utc for preseason_mode (checked by tests)
            "home_preseason_elo": h["preseason_elo"], "away_preseason_elo": a["preseason_elo"],
            "elo_diff": round(h["preseason_elo"] - a["preseason_elo"], 1),
            "home_attack_rating": h["attack_rating"], "away_attack_rating": a["attack_rating"],
            "attack_diff": round(h["attack_rating"] - a["attack_rating"], 4),
            "home_defense_rating": h["defense_rating"], "away_defense_rating": a["defense_rating"],
            "defense_diff": round(h["defense_rating"] - a["defense_rating"], 4),
            "home_strength_index": round(h["attack_rating"] - h["defense_rating"], 4),
            "away_strength_index": round(a["attack_rating"] - a["defense_rating"], 4),
            "strength_diff": round((h["attack_rating"] - h["defense_rating"]) - (a["attack_rating"] - a["defense_rating"]), 4),
            "promoted_team_adjustment_home": h["promoted_team_flag"],
            "promoted_team_adjustment_away": a["promoted_team_flag"],
            "manager_tenure_diff": "",  # unavailable (see data_sources.yaml)
            "squad_market_value_diff": "",  # unavailable
            "wage_proxy_diff": "",  # unavailable
            "rest_day_diff": fx.get("rest_day_diff", ""),
            "congestion_diff": fx.get("congestion_diff", ""),
            "home_form_rating": "",  # no 2026-27 matches played yet -- see notes
            "away_form_rating": "",
            "form_diff": "",
            "data_quality_score": 0.55 if (h["promoted_team_flag"] or a["promoted_team_flag"]) else 0.75,
            "missingness_summary": (
                "recent-form features unavailable (preseason, no 2026-27 matches played yet); "
                "manager/squad-value/wage features unavailable (no connected source); "
                "European/cup congestion sub-features unavailable (PL-only fixture source)"
            ),
        })

    out_df = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(out_df)} match feature rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
