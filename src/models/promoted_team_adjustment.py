"""Historical promoted-team baseline, computed from real EPL results.

Identifies every team that appeared in a season but not the previous
one within `data/raw/epl_historical_matches.csv` (2015/16-2025/26; the
first season in the dataset, 2014/15, has no prior season to compare
against so promotion status there is unknown and excluded). For each
promoted team-season, computes final points, goal difference, and
whether the team was relegated that same season. These real, observed
outcomes become the prior used to seed 2026-27's three promoted clubs
(Coventry City, Ipswich Town, Hull City) with appropriately wide
uncertainty, per spec section 12.
"""
from __future__ import annotations

import pandas as pd

RELEGATION_ZONE_SIZE = 3


def _season_table(season_matches: pd.DataFrame) -> pd.DataFrame:
    teams = sorted(set(season_matches["home_team"]) | set(season_matches["away_team"]))
    stats = {t: {"points": 0, "goals_for": 0, "goals_against": 0, "played": 0} for t in teams}
    for _, m in season_matches.iterrows():
        h, a = m["home_team"], m["away_team"]
        hg, ag = int(m["home_goals"]), int(m["away_goals"])
        stats[h]["goals_for"] += hg
        stats[h]["goals_against"] += ag
        stats[a]["goals_for"] += ag
        stats[a]["goals_against"] += hg
        stats[h]["played"] += 1
        stats[a]["played"] += 1
        if hg > ag:
            stats[h]["points"] += 3
        elif hg < ag:
            stats[a]["points"] += 3
        else:
            stats[h]["points"] += 1
            stats[a]["points"] += 1
    table = pd.DataFrame.from_dict(stats, orient="index").reset_index().rename(columns={"index": "team"})
    table["goal_difference"] = table["goals_for"] - table["goals_against"]
    table = table.sort_values(["points", "goal_difference", "goals_for"], ascending=False).reset_index(drop=True)
    table["final_rank"] = table.index + 1
    return table


def compute_promoted_team_history(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per real historical promoted-team-season with real outcomes."""
    matches = matches.dropna(subset=["home_goals", "away_goals"])
    seasons = list(dict.fromkeys(matches.sort_values("date")["season"]))

    teams_by_season = {
        s: set(matches[matches["season"] == s]["home_team"]) | set(matches[matches["season"] == s]["away_team"])
        for s in seasons
    }
    tables_by_season = {s: _season_table(matches[matches["season"] == s]) for s in seasons}

    rows = []
    for i in range(1, len(seasons)):
        prev_s, cur_s = seasons[i - 1], seasons[i]
        promoted = teams_by_season[cur_s] - teams_by_season[prev_s]
        if not promoted:
            continue
        table = tables_by_season[cur_s]
        n_teams = len(table)
        league_avg_points = table["points"].mean()
        for team in promoted:
            row = table[table["team"] == team].iloc[0]
            rows.append({
                "season": cur_s,
                "team": team,
                "final_rank": int(row["final_rank"]),
                "points": int(row["points"]),
                "goal_difference": int(row["goal_difference"]),
                "goals_for": int(row["goals_for"]),
                "goals_against": int(row["goals_against"]),
                "league_avg_points_same_season": round(league_avg_points, 1),
                "points_below_league_avg": round(row["points"] - league_avg_points, 1),
                "relegated_same_season": bool(row["final_rank"] > n_teams - RELEGATION_ZONE_SIZE),
            })
    return pd.DataFrame(rows)


def summarize_promoted_team_baseline(history: pd.DataFrame) -> dict:
    if history.empty:
        return {
            "n_promotion_events": 0,
            "mean_points": None,
            "mean_points_below_league_avg": None,
            "mean_goal_difference": None,
            "relegation_rate": None,
        }
    return {
        "n_promotion_events": len(history),
        "mean_points": round(history["points"].mean(), 1),
        "mean_points_below_league_avg": round(history["points_below_league_avg"].mean(), 1),
        "mean_goal_difference": round(history["goal_difference"].mean(), 1),
        "relegation_rate": round(history["relegated_same_season"].mean(), 3),
    }
