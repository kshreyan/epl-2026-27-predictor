"""Collect real historical UEFA Nations League results, the one real
prior cycle fixturedownload.com publishes (2024-25).

Source: fixturedownload.com's public JSON feed
(https://fixturedownload.com/feed/json/nations-league-2024) -- the
same source (and fixture-shaped JSON format) the generic fixtures
collector (collect_fixtures.py) uses for the current 2026-27 cycle.
Confirmed directly this session: 2018/2020/2022 editions are still not
published there (404), same real gap as when this competition was
first built -- this is genuinely thin real data (168 real matches, one
of them a real abandoned fixture with no score) versus a domestic
league's 2,000+, or even UCL/UEL/UECL's two real Swiss-era cycles.
Model reports built from this data must say so plainly, not imply the
same statistical confidence domestic leagues have.

Not collect_continental_cup_historical.py: that collector is hard-
coupled to the 36-team Swiss-model league-phase structure (2024-25
onward only, because the format itself changed that year) and pulls a
fixed 2-cycle window. Nations League has used the same real group
format since 2018 -- there was never a format change -- but
fixturedownload.com's own real coverage gap (no pre-2024 editions)
means only one cycle is actually collectible regardless.

Writes real `round_number`/`stage` columns in the same shape
backtest_continental_cup.py/predict_continental_cup_matches.py already
expect from the Swiss competitions, so this league can reuse those
modules unchanged: real rounds 1-6 are the group stage (`league_phase`,
confirmed directly against the live feed), rounds 7-10 are the real
knockout stage (quarterfinals/semis, the final/3rd-place match) that
followed in March and June 2025.

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
from src.leagues import league_path, load_league_config  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAGUE_ID = "nations_league"
SOURCE_NAME = "fixturedownload.com"
SOURCE_URL = "https://fixturedownload.com/feed/json/nations-league-2024"
SEASON_LABEL = "2024-25"
RAW_CACHE_PATH = REPO_ROOT / "data" / "external" / "fixturedownload_nations_league_2024_25.json"
LEAGUE_PHASE_ROUNDS = 6  # real matchdays 1-6; confirmed directly against the live feed

ABANDONED_MATCH_NUMBER = 116  # Romania v Kosovo, 2024-11-15 -- see module docstring

OUTPUT_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team",
    "round_number", "stage", "group",
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


def stage_for_round(round_number: int) -> str:
    return "league_phase" if round_number <= LEAGUE_PHASE_ROUNDS else "knockout"


def main() -> None:
    cfg = load_league_config(LEAGUE_ID)
    output_path = REPO_ROOT / "data" / "raw" / league_path(LEAGUE_ID, "historical_matches.csv")

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
        round_number = int(m["RoundNumber"])

        match_id = f"{cfg.match_id_prefix}2425_R{round_number:02d}_{m['MatchNumber']:03d}_{home.replace(' ', '')}_{away.replace(' ', '')}"

        rows.append({
            "season": SEASON_LABEL, "match_id": match_id, "date": dt_utc.strftime("%Y-%m-%d"),
            "home_team": home, "away_team": away,
            "round_number": round_number, "stage": stage_for_round(round_number), "group": m.get("Group") or "",
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
        f"({n_league_phase} league phase, {n_knockout} knockout, {n_abandoned} real abandoned match excluded)"
    )

    log_data_version(
        dataset_name="nations_league_historical_matches",
        source_name=SOURCE_NAME,
        source_timestamp=fetch_ts,
        row_count=len(rows),
        is_real_data=True,
        notes=(
            f"UEFA Nations League {SEASON_LABEL} cycle, the only prior cycle fixturedownload.com publishes "
            f"(confirmed directly: 2018/2020/2022 editions still return 404) -- genuinely thin ({len(rows)} "
            f"real matches) versus a domestic league's 2,000+. {n_abandoned} real abandoned match "
            f"(Romania v Kosovo, 2024-11-15) excluded, not fabricated."
        ),
    )


if __name__ == "__main__":
    main()
