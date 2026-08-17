"""Builds data/processed/epl_team_strength_baseline.csv (spec section 5.3).

Populates what is genuinely derivable from real data (in-house Elo,
Dixon-Coles attack/defense, promoted-team flag, previous-season
league table position for clubs that were in our historical EPL
dataset last season) and explicitly leaves blank + flags as
unavailable the fields with no connected source (ClubElo/SPI external
ratings, squad market value, wage-bill proxy, manager identity/tenure,
Championship-season stats for clubs whose prior season was outside
the Premier League).

Run: python -m src.features.build_team_strength_features
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.elo_model import compute_promoted_team_elo_offset, run_elo  # noqa: E402
from src.models.promoted_team_adjustment import compute_promoted_team_history  # noqa: E402
from src.models.scoreline_models import apply_promoted_team_adjustment, fit_dixon_coles_model  # noqa: E402
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
OUT_PATH = REPO_ROOT / "data" / "processed" / "epl_team_strength_baseline.csv"

PROMOTED_TEAMS = ["Coventry City", "Ipswich Town", "Hull City"]
SEASON = "2026-27"
LAST_COMPLETED_SEASON = "2025-26"

COLUMNS = [
    "team", "season", "preseason_elo", "clubelo_rating_if_available", "spi_rating_if_available",
    "attack_rating", "defense_rating", "home_attack_rating", "home_defense_rating",
    "away_attack_rating", "away_defense_rating", "promoted_team_flag", "previous_season_league",
    "previous_season_finish", "previous_season_points", "previous_season_goal_difference",
    "previous_season_xg_difference", "squad_market_value", "wage_bill_proxy", "manager",
    "manager_start_date", "manager_tenure_days", "source_name", "source_timestamp",
    "data_quality_score", "notes",
]


def previous_season_table(matches: pd.DataFrame, season: str) -> pd.DataFrame:
    season_matches = matches[matches["season"] == season].dropna(subset=["home_goals", "away_goals"])
    teams = sorted(set(season_matches["home_team"]) | set(season_matches["away_team"]))
    stats = {t: {"points": 0, "gf": 0, "ga": 0} for t in teams}
    for _, m in season_matches.iterrows():
        h, a, hg, ag = m["home_team"], m["away_team"], m["home_goals"], m["away_goals"]
        stats[h]["gf"] += hg
        stats[h]["ga"] += ag
        stats[a]["gf"] += ag
        stats[a]["ga"] += hg
        if hg > ag:
            stats[h]["points"] += 3
        elif hg < ag:
            stats[a]["points"] += 3
        else:
            stats[h]["points"] += 1
            stats[a]["points"] += 1
    table = pd.DataFrame.from_dict(stats, orient="index").reset_index().rename(columns={"index": "team"})
    table["gd"] = table["gf"] - table["ga"]
    table = table.sort_values(["points", "gd", "gf"], ascending=False).reset_index(drop=True)
    table["finish"] = table.index + 1
    return table.set_index("team")


def main() -> None:
    with open(MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)

    df = pd.read_csv(HISTORICAL_PATH, parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))

    promoted_elo_offset, n_events = compute_promoted_team_elo_offset(df_clean)
    elo_run = run_elo(df_clean, promoted_offset=promoted_elo_offset)
    elo_final = elo_run.final_ratings

    promo_history = compute_promoted_team_history(df_clean)
    points_shortfall_by_avg = promo_history["points_below_league_avg"].mean() if not promo_history.empty else -15.0
    # Both offsets share the sign of points_shortfall_by_avg (negative for a
    # below-average team): lower attack = scores less, and since defense[i]
    # is SUBTRACTED in the Dixon-Coles exponent (higher defense = concedes
    # fewer goals), a lower defense value also means concedes MORE -- both
    # offsets pointing the same (negative) direction is what makes a
    # promoted team weaker on both ends, not stronger on one.
    dc_attack_offset = points_shortfall_by_avg / 100.0
    dc_defense_offset = points_shortfall_by_avg / 100.0

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    fit = fit_dixon_coles_model(
        df_clean, universe, as_of_date, half_life_days=model_cfg["dixon_coles"]["time_decay_half_life_days"],
    )
    fit = apply_promoted_team_adjustment(fit, PROMOTED_TEAMS, dc_attack_offset, dc_defense_offset)

    prev_table = previous_season_table(df_clean, LAST_COMPLETED_SEASON)
    generated_at = now_utc_iso()

    rows = []
    for team in EPL_2026_27_CLUBS:
        is_promoted = team in PROMOTED_TEAMS
        i = fit.team_index[team]
        attack, defense = float(fit.attack[i]), float(fit.defense[i])

        prev_row = prev_table.loc[team] if team in prev_table.index else None
        notes_parts = []
        if is_promoted:
            notes_parts.append(
                f"Promoted club; previous season was Championship, not Premier League -- no verified "
                f"Championship results source connected, so previous_season_* Championship fields are blank. "
                f"Elo/attack/defense seeded using the empirical promoted-team offset derived from "
                f"{n_events} real historical promotion events (points_below_league_avg={points_shortfall_by_avg:.1f})."
            )
        if prev_row is None and not is_promoted:
            notes_parts.append("No previous-season EPL row found in historical dataset.")
        notes_parts.append("clubelo_rating_if_available/spi_rating_if_available/squad_market_value/"
                            "wage_bill_proxy/manager fields unavailable -- no connected source (see data_sources.yaml).")

        rows.append({
            "team": team,
            "season": SEASON,
            "preseason_elo": round(elo_final.get(team, 1500.0), 1),
            "clubelo_rating_if_available": "",
            "spi_rating_if_available": "",
            "attack_rating": round(attack, 4),
            "defense_rating": round(defense, 4),
            "home_attack_rating": round(attack + fit.home_advantage / 2, 4),
            "home_defense_rating": round(defense, 4),
            "away_attack_rating": round(attack, 4),
            "away_defense_rating": round(defense - fit.home_advantage / 2, 4),
            "promoted_team_flag": is_promoted,
            "previous_season_league": "Championship" if is_promoted else ("Premier League" if prev_row is not None else ""),
            "previous_season_finish": int(prev_row["finish"]) if prev_row is not None else "",
            "previous_season_points": int(prev_row["points"]) if prev_row is not None else "",
            "previous_season_goal_difference": int(prev_row["gd"]) if prev_row is not None else "",
            "previous_season_xg_difference": "",
            "squad_market_value": "",
            "wage_bill_proxy": "",
            "manager": "",
            "manager_start_date": "",
            "manager_tenure_days": "",
            "source_name": "in-house Elo + Dixon-Coles fit on football-data.co.uk historical results",
            "source_timestamp": generated_at,
            "data_quality_score": 0.55 if is_promoted else 0.75,
            "notes": " ".join(notes_parts),
        })

    out_df = pd.DataFrame(rows)[COLUMNS]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"Wrote team strength baseline for {len(out_df)} teams to {OUT_PATH}")


if __name__ == "__main__":
    main()
