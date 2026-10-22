"""Shared real-data fetch helpers for ESPN's public site API
(site.api.espn.com), the single real source this project uses for both
current-season fixtures AND historical results for NFL and NBA -- no
`fixturedownload.com` equivalent exists for American team sports (see
config/leagues.yaml). Verified directly accessible this session, real
schedule/score data, no auth required.

Uses the per-TEAM schedule endpoint
(sports/{sport}/{league}/teams/{id}/schedule?season=YYYY), not a
day-by-day scoreboard scan: one request per team returns that team's
entire real season (confirmed: 17 games for an NFL team, 82 for an
NBA team), versus ~20-170+ requests scanning every calendar date.
Each real game appears in two teams' schedules (home and away) --
deduplicated by ESPN's own real event id.

`season` follows ESPN's own convention (the LATER calendar year of a
split season, e.g. season=2026 is the real 2025-26 NBA season / the
real 2026 NFL season) -- not this project's "2026-27" label; callers
translate as needed.

Explicitly NOT Basketball-Reference (an alternative NBA historical
source): same Sports-Reference family as FBref, whose Terms of Use
this project already determined prohibit scraping/building a tool
from -- same reasoning applies, avoided for consistency.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import load_league_config  # noqa: E402

ESPN_SPORT_PATH = {"nfl": "football/nfl", "nba": "basketball/nba"}
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_real_teams(league_id: str) -> list[dict]:
    """Real team id -> displayName, straight from ESPN -- no hardcoded
    roster (unlike team_names.py's CANONICAL_TEAMS, which still owns
    the canonical spelling and alias resolution; this is just id
    discovery)."""
    sport_path = ESPN_SPORT_PATH[league_id]
    resp = requests.get(
        f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams",
        params={"limit": 50}, headers=HEADERS, timeout=30,
    )
    resp.raise_for_status()
    teams = resp.json()["sports"][0]["leagues"][0]["teams"]
    return [{"id": t["team"]["id"], "display_name": t["team"]["displayName"]} for t in teams]


def fetch_real_season_games(league_id: str, season: int) -> list[dict]:
    """Every real regular-season game for `season` (ESPN's year
    convention -- see module docstring), deduplicated across all teams'
    schedules. Each returned dict: event_id, date (ISO UTC), home_team,
    away_team, home_score, away_score (None if not yet played),
    completed (bool), week_number (NFL only, else None), venue."""
    cfg = load_league_config(league_id)
    sport_path = ESPN_SPORT_PATH[league_id]
    teams = fetch_real_teams(league_id)
    if len(teams) != cfg.n_teams:
        raise ValueError(
            f"Expected {cfg.n_teams} real {league_id} teams from ESPN, got {len(teams)}. "
            f"Refusing to proceed with a team list that doesn't match the real league."
        )

    games: dict[str, dict] = {}
    for t in teams:
        resp = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{t['id']}/schedule",
            params={"season": season}, headers=HEADERS, timeout=30,
        )
        resp.raise_for_status()
        events = resp.json().get("events", [])
        for ev in events:
            if ev.get("seasonType", {}).get("type") != 2:
                continue  # real regular season only -- excludes real preseason/postseason games
            event_id = ev["id"]
            if event_id in games:
                continue
            comp = ev["competitions"][0]
            home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
            away = next(c for c in comp["competitors"] if c["homeAway"] == "away")
            status = comp["status"]["type"]

            def _score(side: dict) -> int | None:
                # The team-schedule endpoint nests the real score as
                # {"value": N, "displayValue": "N"}, unlike the
                # scoreboard endpoint's plain number -- handle both
                # shapes defensively rather than assuming one.
                s = side.get("score")
                if s is None:
                    return None
                if isinstance(s, dict):
                    s = s.get("value")
                return int(s) if s is not None else None

            games[event_id] = {
                "event_id": event_id,
                "date": ev["date"],
                "home_team": home["team"]["displayName"],
                "away_team": away["team"]["displayName"],
                "home_score": _score(home) if status.get("completed") else None,
                "away_score": _score(away) if status.get("completed") else None,
                "completed": bool(status.get("completed")),
                "week_number": ev.get("week", {}).get("number"),
                "venue": comp.get("venue", {}).get("fullName", ""),
            }
    return sorted(games.values(), key=lambda g: g["date"])
