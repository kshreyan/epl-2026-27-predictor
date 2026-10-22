"""Collect real historical NFL/NBA results from ESPN's site API (see
espn_api.py for source rationale), several real past regular seasons.

Columns are named `home_score`/`away_score`, not `home_goals`/
`away_goals` -- these are real POINTS, not goals, and this project
never relabels a real unit to make it fit an existing schema. Callers
that reuse goal-based soccer code (e.g. `elo_model.run_elo`, which
only needs matching column names, not a specific unit) rename these
two columns at the call site; the real stored data stays honestly
labeled.

No play-by-play/box-score stats (passing yards, shooting splits, etc.)
-- ESPN's schedule endpoint doesn't carry them and this project does
not estimate what it can't source for real.

Run: python -m src.data_collection.collect_espn_historical --league nfl
(also accepts nba)
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_collection.espn_api import fetch_real_season_games  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "site.api.espn.com"

# ESPN's own season-year convention (see collect_espn_schedule.py) --
# the N most recent real COMPLETED seasons before the current one.
CURRENT_SEASON = {"nfl": 2026, "nba": 2027}
N_PRIOR_SEASONS = 5

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "week_number",
    "home_score", "away_score", "result",
    "venue", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

UNAVAILABLE_NOTE = "Play-by-play/box-score stats are not published by ESPN's schedule endpoint and are intentionally omitted rather than estimated."


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    output_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")

    current = CURRENT_SEASON[league_id]
    seasons = list(range(current - N_PRIOR_SEASONS, current))

    rows = []
    fetch_ts = now_utc_iso()
    for espn_season in seasons:
        games = fetch_real_season_games(league_id, espn_season)
        season_label = f"{espn_season - 1}-{str(espn_season)[2:]}" if league_id == "nba" else f"{espn_season}"
        n_this_season = 0
        for g in games:
            if not g["completed"] or g["home_score"] is None or g["away_score"] is None:
                continue  # a real past season should be fully played out; skip rather than fabricate
            home = normalize_team_name(g["home_team"], league_id=league_id)
            away = normalize_team_name(g["away_team"], league_id=league_id)
            dt_utc = datetime.fromisoformat(g["date"].replace("Z", "+00:00"))
            result = "home_win" if g["home_score"] > g["away_score"] else ("away_win" if g["away_score"] > g["home_score"] else "draw")
            match_id = f"{cfg.match_id_prefix}{espn_season}_{g['event_id']}_{home.replace(' ', '')}_{away.replace(' ', '')}"
            rows.append({
                "season": season_label, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
                "home_team": home, "away_team": away, "week_number": g["week_number"] or "",
                "home_score": g["home_score"], "away_score": g["away_score"], "result": result,
                "venue": g["venue"], "source_name": SOURCE_NAME,
                "source_url_or_page_title": f"https://site.api.espn.com/apis/site/v2/sports/.../{league_id}/teams/{{id}}/schedule?season={espn_season}",
                "source_timestamp": fetch_ts, "is_real_data": True, "data_status": "completed",
                "notes": UNAVAILABLE_NOTE,
            })
            n_this_season += 1
        print(f"  season={espn_season} ({season_label}): {n_this_season} real completed games")

    rows.sort(key=lambda r: r["date"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real historical games to {output_path} ({seasons[0]}-{seasons[-1]})")

    log_data_version(
        dataset_name=f"{league_id}_historical_matches", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(rows), is_real_data=True,
        notes=f"{cfg.display_name}, {len(seasons)} real prior regular seasons from ESPN's site API.",
    )


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
