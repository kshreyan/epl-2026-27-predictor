"""Collect real historical results for a UEFA club competition (UCL,
UEL, or UECL), two prior real seasons (2024-25, 2025-26) -- the only
two cycles played under the current 36-team Swiss-model league phase
(the format changed in 2024-25, so nothing older is comparable; see
config/leagues.yaml). Generalizes the old, now-removed
collect_nations_league_historical.py (one competition, one cycle) to
three competitions, two cycles each.

Source: fixturedownload.com's public JSON feed, the same source (and
shape) the current-season fixtures collector uses, one and two years
back (e.g. https://fixturedownload.com/feed/json/champions-league-2024
and -2025). No football-data.co.uk coverage exists for any UEFA club
competition (football_data_code is intentionally None in
config/leagues.yaml) -- this is a bespoke collector, not
collect_historical_results.py.

Pulls EVERY real match each season's feed has, not just the league
phase -- the knockout rounds that followed it (confirmed real, fully
scored: playoff round through the Final) are real signal about team
strength too and are kept for fitting. `round_number` and `stage`
columns let a consumer separate "league phase" (round<=8, or <=6 for
UECL) from "knockout" matches explicitly rather than guessing from
date alone. Whether/how predict_continental_cup_matches.py and
backtest_continental_cup.py use the knockout rows is each of those
scripts' own, separate decision -- this collector's only job is making
the real data available, unfiltered.

Run: python -m src.data_collection.collect_continental_cup_historical --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "fixturedownload.com"
HISTORICAL_SEASON_YEARS = [2024, 2025]  # -> real 2024-25, 2025-26 cycles

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team",
    "round_number", "stage",
    "home_goals", "away_goals", "result",
    "home_xg", "away_xg",
    "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession",
    "home_ppda", "away_ppda",
    "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg",
    "home_red_cards", "away_red_cards",
    "referee", "stadium", "attendance",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

UNAVAILABLE_NOTE = (
    "Advanced metrics (xG, possession, PPDA, big_chances, set_piece_xg), referee, and attendance are "
    "not published by fixturedownload.com and are intentionally left blank rather than estimated."
)


def stage_for_round(round_number: int, league_phase_rounds: int) -> str:
    return "league_phase" if round_number <= league_phase_rounds else "knockout"


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    league_phase_rounds = (cfg.expected_fixture_count or 0) // (cfg.n_teams // 2)
    output_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")

    rows = []
    for year in HISTORICAL_SEASON_YEARS:
        season_label = f"{year}-{str(year + 1)[2:]}"
        source_url = f"https://fixturedownload.com/feed/json/{cfg.fixturedownload_slug}-{year}"
        raw_cache_path = REPO_ROOT / "data" / "external" / f"fixturedownload_{league_id}_{year}.json"

        fetch_ts = now_utc_iso()
        resp = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        resp.raise_for_status()
        raw_cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw_cache_path.write_bytes(resp.content)
        matches = resp.json()

        for m in matches:
            if m["HomeTeamScore"] is None or m["AwayTeamScore"] is None:
                raise ValueError(
                    f"Unexpected unscored real match in {cfg.display_name} {season_label}: "
                    f"MatchNumber {m['MatchNumber']} ({m['HomeTeam']} v {m['AwayTeam']}). "
                    f"Investigate before silently dropping it."
                )

            home = normalize_team_name(m["HomeTeam"], league_id=league_id)
            away = normalize_team_name(m["AwayTeam"], league_id=league_id)
            dt_utc = datetime.strptime(m["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
            home_goals, away_goals = int(m["HomeTeamScore"]), int(m["AwayTeamScore"])
            result = "home_win" if home_goals > away_goals else ("away_win" if away_goals > home_goals else "draw")
            round_number = int(m["RoundNumber"])

            match_id = (
                f"{cfg.match_id_prefix}{str(year)[2:]}{str(year + 1)[2:]}_R{round_number:02d}_"
                f"{m['MatchNumber']:03d}_{home.replace(' ', '')}_{away.replace(' ', '')}"
            )

            rows.append({
                "season": season_label, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
                "home_team": home, "away_team": away,
                "round_number": round_number, "stage": stage_for_round(round_number, league_phase_rounds),
                "home_goals": home_goals, "away_goals": away_goals, "result": result,
                "home_xg": "", "away_xg": "",
                "home_shots": "", "away_shots": "", "home_shots_on_target": "", "away_shots_on_target": "",
                "home_possession": "", "away_possession": "",
                "home_ppda": "", "away_ppda": "",
                "home_big_chances": "", "away_big_chances": "",
                "home_set_piece_xg": "", "away_set_piece_xg": "",
                "home_red_cards": "", "away_red_cards": "",
                "referee": "", "stadium": m.get("Location") or "", "attendance": "",
                "source_name": SOURCE_NAME, "source_url_or_page_title": source_url, "source_timestamp": fetch_ts,
                "is_real_data": True, "data_status": "completed", "notes": UNAVAILABLE_NOTE,
            })

    rows.sort(key=lambda r: r["date"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    n_league_phase = sum(1 for r in rows if r["stage"] == "league_phase")
    n_knockout = len(rows) - n_league_phase
    print(
        f"Wrote {len(rows)} real historical matches to {output_path} "
        f"({n_league_phase} league phase, {n_knockout} knockout, across {HISTORICAL_SEASON_YEARS})"
    )

    log_data_version(
        dataset_name=f"{league_id}_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=now_utc_iso(),
        row_count=len(rows),
        is_real_data=True,
        notes=(
            f"{cfg.display_name}, real 2024-25 + 2025-26 cycles (the only two seasons under the "
            f"current 36-team Swiss-model format) -- genuinely thin versus a domestic league's "
            f"2,000+ real matches."
        ),
    )


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
