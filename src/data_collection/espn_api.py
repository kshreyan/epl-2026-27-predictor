"""Shared real-data fetch helpers for ESPN's public site API
(site.api.espn.com), the single real source this project uses for both
current-season fixtures AND historical results for NFL, NBA, and
NCAA Football -- no `fixturedownload.com` equivalent exists for
American team sports (see config/leagues.yaml). Verified directly
accessible this session, real schedule/score data, no auth required.

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

ESPN_SPORT_PATH = {
    "nfl": "football/nfl", "nba": "basketball/nba",
    "ncaaf": "football/college-football",
}
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_real_fbs_conferences() -> dict[str, list[dict]]:
    """Real FBS conference -> [{"id", "display_name"}] for every real
    team in it, straight from ESPN's own live standings -- confirmed
    directly this session as the only reliable real source for this
    (the generic /teams?groups=80 endpoint does NOT actually filter to
    FBS -- confirmed directly, it silently includes real Division III
    teams like Amherst). Recurses through each conference's real
    sub-structure (most conferences list teams directly; some, e.g. the
    real Sun Belt Conference this season, nest them one level deeper
    under real East/West divisions) rather than assuming a fixed depth,
    since that nesting is itself a real fact that varies by conference
    and season, not something to hardcode. Not hardcoded like NFL/NBA's
    stable divisions (see simulate_team_sport_season.py) because real
    conference realignment is a recurring event in college sports --
    fetched fresh every call."""
    resp = requests.get(
        "https://site.api.espn.com/apis/v2/sports/football/college-football/standings",
        params={"group": "80"}, headers=HEADERS, timeout=30,
    )
    resp.raise_for_status()
    root = resp.json()

    def _collect(node: dict) -> list[dict]:
        teams = []
        for entry in node.get("standings", {}).get("entries", []):
            teams.append({"id": entry["team"]["id"], "display_name": entry["team"]["displayName"]})
        for child in node.get("children", []):
            teams.extend(_collect(child))
        return teams

    return {conf["name"]: _collect(conf) for conf in root["children"]}


def fetch_real_teams(league_id: str) -> list[dict]:
    """Real team id -> displayName, straight from ESPN -- no hardcoded
    roster (unlike team_names.py's CANONICAL_TEAMS, which still owns
    the canonical spelling and alias resolution; this is just id
    discovery). NCAA Football uses fetch_real_fbs_conferences() instead
    of the generic /teams endpoint -- see that function's docstring for
    why (the generic endpoint's groups filter doesn't reliably isolate
    FBS)."""
    if league_id == "ncaaf":
        teams = [t for roster in fetch_real_fbs_conferences().values() for t in roster]
        seen: dict[str, dict] = {t["id"]: t for t in teams}  # a handful of teams appear in more than one FBS feed this season (e.g. independents); de-duplicate by real team id
        return list(seen.values())
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
    # NCAA Football's real FBS roster isn't a fixed closed set the way
    # NFL/NBA's is -- real transitioning programs join/leave FBS
    # mid-cycle, so cfg.n_teams is a real recent snapshot, not an
    # eternal constant; a wide sanity band catches a genuinely broken
    # fetch without false-alarming on normal roster drift.
    if league_id == "ncaaf":
        if not (100 <= len(teams) <= 150):
            raise ValueError(f"Expected roughly 100-150 real FBS teams from ESPN, got {len(teams)}. Refusing to proceed.")
    elif len(teams) != cfg.n_teams:
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
