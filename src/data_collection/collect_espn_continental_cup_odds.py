"""Collect real historical closing (and opening) 3-way moneylines for
a UEFA club competition's most recent complete real season (2025-26),
from ESPN's real soccer scoreboard + game-summary endpoints
(site.api.espn.com/.../soccer/{espn_slug}/...) -- confirmed directly
this session: ESPN carries real UCL/UEL odds (DraftKings-sourced
pickcenter, with a real open/close distinction, same shape as
collect_espn_nba_game_detail.py's real NBA source) even though no
football-data.co.uk coverage exists for either competition (see
market_blend_model.py's docstring -- that remains true; this is a
different, until-now-unchecked real source, not a reversal of it).

Scoped to ONE real season, same deliberate-scope-limit discipline as
collect_espn_ncaaf_odds.py and collect_espn_nba_game_detail.py (one
real recent cycle, not all historical seasons) -- a real UCL/UEL
season only has 33/20 distinct real league-phase+knockout matchdays,
so this uses the per-date scoreboard endpoint (fine at this scale),
not espn_api.py's per-team-schedule endpoint.

Matches each real ESPN event to this project's own real match_id
(from fixturedownload.com's historical_matches.csv) by (date,
home_team, away_team) -- both team names normalized through this
competition's own canonical table -- never by team-name alone: the
Ligue 1 double-counting incident (see fetch_live_results.py) is the
exact real reason date is part of the key here too, even though no
repeat-fixture collision is currently known in a single UCL/UEL
season. Raises on any genuine ambiguity rather than guessing.

Run: python -m src.data_collection.collect_espn_continental_cup_odds --league ucl
(also accepts uel)
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "site.api.espn.com (game summary)"
ESPN_SLUG = {"ucl": "uefa.champions", "uel": "uefa.europa"}
MOST_RECENT_SEASON = "2025-26"
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={date}"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/summary?event={event_id}"
REQUEST_TIMEOUT = 20
ODDS_COLUMNS = [
    "match_id",
    "home_moneyline_open", "home_moneyline_close",
    "away_moneyline_open", "away_moneyline_close",
    "draw_moneyline_open", "draw_moneyline_close",
    "source_name", "source_timestamp",
]


def _fetch_espn_events_for_date(slug: str, date_str: str, league_id: str) -> dict[tuple[str, str, str], str]:
    """real (date, home, away) -> real ESPN event id, for every real
    event ESPN's scoreboard has on this real date. Raises on an
    unrecognized ESPN team name rather than silently dropping it."""
    resp = requests.get(SCOREBOARD_URL.format(slug=slug, date=date_str.replace("-", "")), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    out = {}
    for ev in resp.json().get("events", []):
        comp = ev["competitions"][0]
        home_raw = next(c["team"]["displayName"] for c in comp["competitors"] if c["homeAway"] == "home")
        away_raw = next(c["team"]["displayName"] for c in comp["competitors"] if c["homeAway"] == "away")
        home = normalize_team_name(home_raw, league_id=league_id)
        away = normalize_team_name(away_raw, league_id=league_id)
        out[(date_str, home, away)] = ev["id"]
    return out


def _parse_moneyline(summary: dict) -> dict | None:
    pickcenter = summary.get("pickcenter", [])
    if not pickcenter:
        return None
    ml = pickcenter[0].get("moneyline", {})
    home, away, draw = ml.get("home", {}), ml.get("away", {}), ml.get("draw", {})
    if not (home.get("open") and home.get("close") and away.get("open") and away.get("close")):
        return None
    out = {
        "home_moneyline_open": float(home["open"]["odds"]), "home_moneyline_close": float(home["close"]["odds"]),
        "away_moneyline_open": float(away["open"]["odds"]), "away_moneyline_close": float(away["close"]["odds"]),
    }
    if draw.get("open") and draw.get("close"):
        out["draw_moneyline_open"] = float(draw["open"]["odds"])
        out["draw_moneyline_close"] = float(draw["close"]["odds"])
    else:
        out["draw_moneyline_open"] = ""
        out["draw_moneyline_close"] = ""
    return out


def main(league_id: str) -> None:
    slug = ESPN_SLUG[league_id]
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    hist_df = pd.read_csv(historical_path)
    season_games = hist_df[hist_df["season"] == MOST_RECENT_SEASON].copy()
    dates = sorted(season_games["date"].unique())
    print(f"Scanning {len(dates)} real {MOST_RECENT_SEASON} {league_id.upper()} matchdates on ESPN's scoreboard...")

    espn_lookup: dict[tuple[str, str, str], str] = {}
    for d in dates:
        espn_lookup.update(_fetch_espn_events_for_date(slug, d, league_id))
        time.sleep(0.1)

    fetch_ts = now_utc_iso()
    rows = []
    n_matched, n_unmatched, n_no_odds = 0, 0, 0
    for i, (_, row) in enumerate(season_games.iterrows()):
        key = (row["date"], row["home_team"], row["away_team"])
        event_id = espn_lookup.get(key)
        if event_id is None:
            n_unmatched += 1
            continue
        n_matched += 1
        resp = requests.get(SUMMARY_URL.format(slug=slug, event_id=event_id), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        ml = _parse_moneyline(resp.json())
        if ml is None:
            n_no_odds += 1
        else:
            rows.append({
                "match_id": row["match_id"], **ml,
                "source_name": SOURCE_NAME, "source_timestamp": fetch_ts,
            })
        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1}/{len(season_games)} real games checked")
        time.sleep(0.1)

    out_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ODDS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real games with a real closing moneyline to {out_path}")
    print(f"({n_matched} real ESPN events matched by date+team, {n_unmatched} real games had no matching real "
          f"ESPN event, {n_no_odds} matched but had no real posted market)")

    log_data_version(
        dataset_name=f"{league_id}_historical_closing_odds", source_name=SOURCE_NAME, source_timestamp=fetch_ts,
        row_count=len(rows), is_real_data=True,
        notes=f"Real {league_id.upper()} closing+opening 3-way moneyline detail, {MOST_RECENT_SEASON} season only.",
    )


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
