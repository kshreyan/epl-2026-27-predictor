"""Collect real historical UEFA Nations League results, 2024-25 cycle.

Source: fixturedownload.com's public JSON feed
(https://fixturedownload.com/feed/json/nations-league-2024) -- the
same source (and fixture-shaped JSON format) the fixtures collector
uses, one cycle back. This is the ONLY prior Nations League cycle that
source publishes (2018/2020/2022 editions are not available there),
so this is real but genuinely thin: 167 real scored matches, versus
the 2,000+ each domestic league's backtest draws on. Model reports
built from this data must say so plainly rather than implying the same
statistical confidence domestic leagues have.

One real match in this feed has no score: Romania v Kosovo, 2024-11-15
(RoundNumber 5, Group C2) -- a real abandoned fixture (security
incident before kickoff), not a missing-data gap in the source. Kept
out of the historical dataset (a null score is not a real result to
train or backtest on) and reflected here, not silently dropped without
a trace.

No football-data.co.uk coverage exists for this competition (it only
covers domestic leagues) -- this is a bespoke collector, not
`collect_historical_results.py --league nations_league`.

Run: python -m src.data_collection.collect_nations_league_historical
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAGUE_ID = "nations_league"
SOURCE_NAME = "fixturedownload.com"
SOURCE_URL = "https://fixturedownload.com/feed/json/nations-league-2024"
SEASON_LABEL = "2024-25"
RAW_CACHE_PATH = REPO_ROOT / "data" / "external" / "fixturedownload_nations_league_2024_25.json"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "nations_league_historical_matches.csv"

ABANDONED_MATCH_NUMBER = 116  # Romania v Kosovo, 2024-11-15 -- see module docstring

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "group",
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


def main() -> None:
    fetch_ts = now_utc_iso()
    resp = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    RAW_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_CACHE_PATH.write_bytes(resp.content)
    matches = resp.json()

    rows = []
    n_abandoned = 0
    for m in matches:
        if m["HomeTeamScore"] is None or m["AwayTeamScore"] is None:
            if m["MatchNumber"] != ABANDONED_MATCH_NUMBER:
                raise ValueError(
                    f"Unexpected unscored match {m['MatchNumber']} ({m['HomeTeam']} v {m['AwayTeam']}) -- "
                    f"only MatchNumber {ABANDONED_MATCH_NUMBER} (the real abandoned Romania v Kosovo fixture) "
                    f"is expected to have no score. Update ABANDONED_MATCH_NUMBER or investigate."
                )
            n_abandoned += 1
            continue

        home = normalize_team_name(m["HomeTeam"], league_id=LEAGUE_ID)
        away = normalize_team_name(m["AwayTeam"], league_id=LEAGUE_ID)
        dt_utc = datetime.strptime(m["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        home_goals, away_goals = int(m["HomeTeamScore"]), int(m["AwayTeamScore"])
        result = "home_win" if home_goals > away_goals else ("away_win" if away_goals > home_goals else "draw")

        match_id = f"UNL2425_MD{m['RoundNumber']:02d}_{m['MatchNumber']:03d}_{home.replace(' ', '')}_{away.replace(' ', '')}"

        rows.append({
            "season": SEASON_LABEL, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
            "home_team": home, "away_team": away, "group": m.get("Group") or "",
            "home_goals": home_goals, "away_goals": away_goals, "result": result,
            "home_xg": "", "away_xg": "",
            "home_shots": "", "away_shots": "", "home_shots_on_target": "", "away_shots_on_target": "",
            "home_possession": "", "away_possession": "",
            "home_ppda": "", "away_ppda": "",
            "home_big_chances": "", "away_big_chances": "",
            "home_set_piece_xg": "", "away_set_piece_xg": "",
            "home_red_cards": "", "away_red_cards": "",
            "referee": "", "stadium": m.get("Location") or "", "attendance": "",
            "source_name": SOURCE_NAME, "source_url_or_page_title": SOURCE_URL, "source_timestamp": fetch_ts,
            "is_real_data": True, "data_status": "completed", "notes": UNAVAILABLE_NOTE,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real historical matches to {OUTPUT_PATH} ({n_abandoned} real abandoned match excluded)")

    log_data_version(
        dataset_name="nations_league_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=True,
        notes=(
            f"UEFA Nations League {SEASON_LABEL} cycle, the only prior cycle fixturedownload.com publishes -- "
            f"genuinely thin (167 real matches) versus a domestic league's 2,000+. {n_abandoned} real "
            f"abandoned match (Romania v Kosovo, 2024-11-15) excluded, not fabricated."
        ),
    )


if __name__ == "__main__":
    main()
