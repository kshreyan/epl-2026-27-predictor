"""Required column schemas for every raw data file (spec section 5),
used by validate_raw_data.py. Kept as plain dicts (not a heavier schema
library) so this stays dependency-light and easy to diff against the
spec by eye.
"""
from __future__ import annotations

FIXTURES_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "kickoff_local",
    "home_team", "away_team", "stadium", "city", "status",
    "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

HISTORICAL_MATCHES_COLUMNS = [
    "season", "match_id", "date", "home_team", "away_team", "home_goals", "away_goals", "result",
    "home_xg", "away_xg", "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
    "home_possession", "away_possession", "home_ppda", "away_ppda", "home_big_chances", "away_big_chances",
    "home_set_piece_xg", "away_set_piece_xg", "home_red_cards", "away_red_cards", "referee", "stadium",
    "attendance", "source_name", "source_url_or_page_title", "source_timestamp", "is_real_data", "data_status", "notes",
]

SQUADS_TRANSFERS_COLUMNS = [
    "team", "player_name", "position", "age", "nationality", "squad_status", "transfer_type", "from_club",
    "to_club", "fee_reported", "estimated_market_value", "minutes_last_season", "starts_last_season",
    "goals_last_season", "assists_last_season", "xg_last_season", "xa_last_season", "npxg_last_season",
    "defensive_actions_last_season", "progressive_actions_last_season", "set_piece_role", "penalty_taker_flag",
    "goalkeeper_psxg_minus_goals_allowed_if_gk", "importance_score", "source_name", "source_url_or_page_title",
    "source_timestamp", "is_real_data", "data_status", "notes",
]

INJURY_SUSPENSION_COLUMNS = [
    "match_id", "matchweek", "date", "team", "opponent", "player_name", "availability_status", "issue_type",
    "body_part_or_reason", "expected_return", "player_importance", "starter_probability_if_fit",
    "minutes_expectation_if_fit", "impact_score", "source_name", "source_url_or_page_title", "source_timestamp",
    "is_real_data", "data_status", "notes",
]

REAL_ODDS_COLUMNS = [
    "match_id", "season", "matchweek", "date", "kickoff_utc", "home_team", "away_team", "bookmaker", "market_type",
    "opening_home_odds", "opening_draw_odds", "opening_away_odds", "current_home_odds", "current_draw_odds",
    "current_away_odds", "closing_home_odds", "closing_draw_odds", "closing_away_odds",
    "spread_line", "home_spread_odds", "away_spread_odds", "total_line", "over_odds", "under_odds",
    "btts_yes_odds", "btts_no_odds", "odds_snapshot_type", "time_to_kickoff_hours",
    "odds_format", "odds_timestamp", "source_name", "source_url_or_page_title", "is_example", "is_real_data",
    "data_status", "collection_date", "notes",
]

OUTRIGHT_ODDS_COLUMNS = [
    "team", "market_type", "bookmaker", "odds", "implied_probability_raw", "implied_probability_no_vig",
    "odds_timestamp", "source_name", "source_url_or_page_title", "is_example", "is_real_data", "data_status",
    "collection_date", "notes",
]

ALLOWED_FIXTURE_STATUS = {"scheduled", "live", "completed", "postponed", "abandoned", "rescheduled", "scheduled_provisional"}
ALLOWED_AVAILABILITY_STATUS = {"available", "doubtful", "questionable", "injured", "suspended", "rested", "unavailable", "unknown"}
ALLOWED_ISSUE_TYPE = {"injury", "suspension", "illness", "fitness", "tactical_rest", "personal", "unknown"}
ALLOWED_ODDS_SNAPSHOT_TYPE = {"opening", "current", "closing", "unknown"}

RAW_FILE_SCHEMAS = {
    "epl_2026_27_fixtures.csv": (FIXTURES_COLUMNS, 380),
    "epl_historical_matches.csv": (HISTORICAL_MATCHES_COLUMNS, None),
    "epl_2026_27_squads_transfers.csv": (SQUADS_TRANSFERS_COLUMNS, None),
    "epl_2026_27_injury_suspension.csv": (INJURY_SUSPENSION_COLUMNS, None),
    # Row count is inherently variable, not fixed at 380: one sentinel row per
    # (fixture, market_type in {h2h, spreads, totals}) at minimum, plus one
    # additional real row per bookmaker that has actually posted a given
    # market for a given fixture (see collect_odds.py).
    "epl_2026_27_real_odds.csv": (REAL_ODDS_COLUMNS, None),
    "epl_2026_27_outright_odds.csv": (OUTRIGHT_ODDS_COLUMNS, None),
}
