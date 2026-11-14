"""Collect real historical results for a UEFA club competition (UCL
or UEL) as far back as fixturedownload.com's feed actually goes for
each one -- confirmed live, not assumed: UCL back to 2017-18, UEL back
to 2019-20. UECL was dropped from this collector 2026-11-14 (removed
from the project entirely): the competition only started 2021-22, and
this source has no UECL seasons before 2024-25 under any feed slug --
a real source ceiling that left it stuck at 2 real seasons, far too
thin to carry on its own. The pre-2024-25 UCL/UEL seasons used the old
32/48-team group-stage format rather than today's 36-team Swiss-model
league phase, but the real match data (teams, scores, dates) is
exactly as usable for Elo/Dixon-Coles fitting either way -- a goal is
a goal regardless of which stage structure produced the fixture list,
so this collector doesn't draw a line at the format change.

Source: fixturedownload.com's public JSON feed, the same source (and
shape) the current-season fixtures collector uses, one season-slug per
real season (e.g. https://fixturedownload.com/feed/json/champions-league-2024).
No football-data.co.uk coverage exists for any UEFA club competition
(football_data_code is intentionally None in config/leagues.yaml) --
this is a bespoke collector, not collect_historical_results.py.

Pulls EVERY real match each season's feed has, not just the league/
group phase -- the knockout rounds that followed it (confirmed real,
fully scored: playoff round through the Final) are real signal about
team strength too and are kept for fitting. `round_number` and `stage`
columns let a consumer separate the real round-robin phase from
knockout matches explicitly. `stage` is derived from the feed's own
real `Group` field (non-null for every real group/league-phase match,
null for every real knockout match, confirmed directly across both
the old group-stage era and the new Swiss-model era) rather than from
a round-number cutoff -- round-number cutoffs differ by era (old-
format group stage was rounds 1-6 for a group of 4; the new Swiss
league phase is rounds 1-8) and guessing one from current-season
config would silently mislabel every old season's knockout rounds 7-8
as league phase. Whether/how predict_continental_cup_matches.py and
backtest_continental_cup.py use the knockout rows is each of those
scripts' own, separate decision -- this collector's only job is making
the real data available, unfiltered.

Run: python -m src.data_collection.collect_continental_cup_historical --league ucl
(also accepts uel)
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
# Earliest real season year fixturedownload.com's feed actually has for
# each competition -- confirmed live (HTTP 200 vs 404) across a wide
# range of candidate years before picking these, not assumed from when
# each competition itself started.
EARLIEST_SEASON_YEAR = {"ucl": 2017, "uel": 2019}
LATEST_SEASON_YEAR = 2025  # -> real 2025-26, the current season's most recent prior cycle

# Confirmed real, individually-investigated exceptions to "every row in
# a concluded historical season has a real score" -- NOT a general
# escape hatch (an unexpected unscored row outside this set still
# raises below, exactly as before).
KNOWN_UNSCORED_MATCH_NUMBERS = {
    # 2019-20 Europa League Round-of-16 first leg, scheduled 2020-03-12,
    # the exact date UEFA competitions shut down for COVID-19;
    # fixturedownload.com's feed kept these two stale, never-played
    # placeholder rows rather than removing them once UEFA restructured
    # the rest of that season into condensed single-leg matches at
    # neutral venues in August 2020 (confirmed: Sevilla did play, and
    # eliminate, Roma for real that season, just not as this row's
    # two-legged tie).
    ("uel", 2019, 179): "Sevilla v Roma",
    ("uel", 2019, 181): "Internazionale v Getafe",
    # 2021-22 Europa League Round-of-16, both legs (2022-03-10 and
    # -03-17): UEFA expelled every Russian club from its competitions
    # following the February 2022 invasion of Ukraine, mid-tie; RB
    # Leipzig advanced by walkover without playing either leg.
    ("uel", 2021, 115): "Leipzig v Spartak Moskva",
    ("uel", 2021, 125): "Spartak Moskva v Leipzig",
}


def historical_season_years(league_id: str) -> list[int]:
    return list(range(EARLIEST_SEASON_YEAR[league_id], LATEST_SEASON_YEAR + 1))

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


def stage_for_match(group: str | None) -> str:
    """"league_phase" for every real group/round-robin-phase match,
    "knockout" otherwise -- derived from the feed's own real `Group`
    field (non-null exactly for group/league-phase matches, confirmed
    directly across both the old 32/48-team group-stage era and the
    new 36-team Swiss-model era), not from a round-number cutoff that
    would differ by era."""
    return "league_phase" if group else "knockout"


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    output_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")

    rows = []
    for year in historical_season_years(league_id):
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
                if (league_id, year, m["MatchNumber"]) not in KNOWN_UNSCORED_MATCH_NUMBERS:
                    raise ValueError(
                        f"Unexpected unscored real match in {cfg.display_name} {season_label}: "
                        f"MatchNumber {m['MatchNumber']} ({m['HomeTeam']} v {m['AwayTeam']}). "
                        f"Investigate before silently dropping it."
                    )
                print(
                    f"Skipping known stale unscored row in {cfg.display_name} {season_label}: "
                    f"MatchNumber {m['MatchNumber']} ({m['HomeTeam']} v {m['AwayTeam']}) -- see "
                    f"KNOWN_UNSCORED_MATCH_NUMBERS."
                )
                continue

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
                "round_number": round_number, "stage": stage_for_match(m.get("Group")),
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

    years = historical_season_years(league_id)
    n_league_phase = sum(1 for r in rows if r["stage"] == "league_phase")
    n_knockout = len(rows) - n_league_phase
    print(
        f"Wrote {len(rows)} real historical matches to {output_path} "
        f"({n_league_phase} league/group phase, {n_knockout} knockout, across real {years[0]}-{str(years[0]+1)[2:]} "
        f"through {years[-1]}-{str(years[-1]+1)[2:]})"
    )

    log_data_version(
        dataset_name=f"{league_id}_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=now_utc_iso(),
        row_count=len(rows),
        is_real_data=True,
        notes=(
            f"{cfg.display_name}, real {years[0]}-{str(years[0]+1)[2:]} through {years[-1]}-{str(years[-1]+1)[2:]} "
            f"cycles ({len(years)} seasons, as far back as fixturedownload.com's feed goes for this competition) "
            f"-- mixes the old group-stage format with the current 36-team Swiss-model league phase; `stage` "
            f"distinguishes them per match via the feed's own real Group field, not a round-number guess."
        ),
    )


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
