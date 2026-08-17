"""Schedule-congestion features computed purely from the real 2026-27
fixture list (no missing-data issue -- every input here is real).

Phase-1 scope: only Premier League fixtures are in scope (no verified
source for UEFA competition or domestic-cup fixture dates is connected
to this pipeline yet), so the European/cup-match congestion sub-features
required by spec section 16 are left as an explicit `data_status=
unavailable` flag rather than computed from PL-only data pretending to
be the full calendar.
"""
from __future__ import annotations

import pandas as pd


def build_schedule_congestion_features(fixtures_df: pd.DataFrame) -> pd.DataFrame:
    fixtures_df = fixtures_df.copy()
    fixtures_df["kickoff_utc"] = pd.to_datetime(fixtures_df["kickoff_utc"])
    fixtures_df = fixtures_df.sort_values("kickoff_utc").reset_index(drop=True)

    last_match_date: dict[str, pd.Timestamp] = {}
    last_7_window: dict[str, list[pd.Timestamp]] = {}
    rows = []

    for _, fx in fixtures_df.iterrows():
        home, away, kickoff = fx["home_team"], fx["away_team"], fx["kickoff_utc"]
        row = {"match_id": fx["match_id"]}

        for side, team in (("home", home), ("away", away)):
            prev = last_match_date.get(team)
            rest_days = (kickoff - prev).days if prev is not None else None
            row[f"{side}_rest_days"] = rest_days

            window = last_7_window.get(team, [])
            window = [d for d in window if (kickoff - d).days <= 14]
            row[f"{side}_matches_last_7_days"] = sum(1 for d in window if (kickoff - d).days <= 7)
            row[f"{side}_matches_last_14_days"] = len(window)
            last_7_window[team] = window

        row["rest_day_diff"] = (
            (row["home_rest_days"] - row["away_rest_days"])
            if row["home_rest_days"] is not None and row["away_rest_days"] is not None else None
        )
        row["congestion_diff"] = row["home_matches_last_7_days"] - row["away_matches_last_7_days"]
        row["home_european_match_last_7_days"] = ""  # not available in Phase 1 (see module docstring)
        row["away_european_match_last_7_days"] = ""
        row["home_cup_match_last_7_days"] = ""
        row["away_cup_match_last_7_days"] = ""
        row["european_cup_data_status"] = "unavailable"
        rows.append(row)

        last_match_date[home] = kickoff
        last_match_date[away] = kickoff
        last_7_window.setdefault(home, []).append(kickoff)
        last_7_window.setdefault(away, []).append(kickoff)

    return pd.DataFrame(rows)
