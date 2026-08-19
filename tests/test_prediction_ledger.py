"""Tests the append-only prediction ledger: an existing row must never
be mutated by a later write, and a prediction selected for scoring must
provably predate that match's own kickoff (the leak-check)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.prediction_ledger import (  # noqa: E402
    LEDGER_COLUMNS,
    append_to_ledger,
    load_combined_match_odds,
    load_live_match_odds,
    load_real_match_odds,
    read_ledger,
    select_pre_kickoff_predictions,
)


def _pred_row(match_id, generated_at, kickoff_utc="2026-08-22T15:00:00+00:00", home_win=0.5, matchweek=1):
    return {
        "match_id": match_id, "matchweek": matchweek, "home_team": "Arsenal", "away_team": "Chelsea",
        "kickoff_utc": kickoff_utc,
        "home_win_prob_model_only": home_win, "draw_prob_model_only": (1 - home_win) / 2,
        "away_win_prob_model_only": (1 - home_win) / 2,
        "dc_raw_home_win_prob": home_win, "dc_raw_draw_prob": (1 - home_win) / 2, "dc_raw_away_win_prob": (1 - home_win) / 2,
        "home_win_prob_market_integrated": "", "draw_prob_market_integrated": "", "away_win_prob_market_integrated": "",
        "market_available": False, "prediction_mode": "preseason_mode", "run_id": f"run_{generated_at}",
        "model_version": "0.1.0-phase1", "generated_at": generated_at,
    }


def test_append_creates_file_with_header_once(tmp_path):
    ledger_path = tmp_path / "ledger.csv"
    append_to_ledger([_pred_row("m1", "2026-08-18T00:00:00+00:00")], ledger_path)
    append_to_ledger([_pred_row("m2", "2026-08-18T00:00:01+00:00")], ledger_path)

    lines = ledger_path.read_text().splitlines()
    header_lines = [l for l in lines if l.startswith("match_id,")]
    assert len(header_lines) == 1  # header written exactly once, not per-append

    df = read_ledger(ledger_path)
    assert list(df.columns) == LEDGER_COLUMNS
    assert len(df) == 2


def test_append_never_mutates_an_existing_row(tmp_path):
    """The core append-only guarantee: after a second append, every byte
    of every previously-written row must be identical to what it was
    before -- not just 'the values still look right after reparsing',
    but the literal file content for those rows is untouched."""
    ledger_path = tmp_path / "ledger.csv"
    append_to_ledger([_pred_row("m1", "2026-08-18T00:00:00+00:00", home_win=0.41)], ledger_path)
    content_after_first_write = ledger_path.read_text()

    # A second, later run appends a fresh prediction for a DIFFERENT match.
    append_to_ledger([_pred_row("m2", "2026-08-19T00:00:00+00:00", home_win=0.62)], ledger_path)
    content_after_second_write = ledger_path.read_text()

    assert content_after_second_write.startswith(content_after_first_write)

    # And appending a NEW prediction for the SAME match_id (a legitimate
    # weekly refresh) must add a new row, never touch the old one.
    append_to_ledger([_pred_row("m1", "2026-08-20T00:00:00+00:00", home_win=0.77)], ledger_path)
    df = read_ledger(ledger_path)
    m1_rows = df[df["match_id"] == "m1"]
    assert len(m1_rows) == 2
    assert set(m1_rows["home_win_prob"]) == {0.41, 0.77}


def test_select_pre_kickoff_predictions_picks_latest_valid_row(tmp_path):
    ledger_path = tmp_path / "ledger.csv"
    kickoff = "2026-08-22T15:00:00+00:00"
    # Three refreshes for the same match, all before kickoff -- should
    # pick the LAST one (0.55), not the first (0.40) or an average.
    append_to_ledger([_pred_row("m1", "2026-08-15T00:00:00+00:00", kickoff, home_win=0.40)], ledger_path)
    append_to_ledger([_pred_row("m1", "2026-08-18T00:00:00+00:00", kickoff, home_win=0.48)], ledger_path)
    append_to_ledger([_pred_row("m1", "2026-08-21T00:00:00+00:00", kickoff, home_win=0.55)], ledger_path)

    ledger = read_ledger(ledger_path)
    selected = select_pre_kickoff_predictions(ledger)
    assert len(selected) == 1
    assert selected.iloc[0]["home_win_prob"] == 0.55


def test_select_pre_kickoff_predictions_ignores_post_kickoff_rows(tmp_path):
    """A weekly-update run happening to fire again after kickoff (e.g. a
    late correction) must never have that later row picked for scoring
    -- the leak this whole module exists to prevent."""
    ledger_path = tmp_path / "ledger.csv"
    kickoff = "2026-08-22T15:00:00+00:00"
    append_to_ledger([_pred_row("m1", "2026-08-20T00:00:00+00:00", kickoff, home_win=0.50)], ledger_path)
    # This row was generated AFTER kickoff -- e.g. a bug, or a refit that
    # already saw the real result. Must never be selected.
    append_to_ledger([_pred_row("m1", "2026-08-23T00:00:00+00:00", kickoff, home_win=0.99)], ledger_path)

    ledger = read_ledger(ledger_path)
    selected = select_pre_kickoff_predictions(ledger)
    assert len(selected) == 1
    assert selected.iloc[0]["home_win_prob"] == 0.50


def test_select_pre_kickoff_predictions_raises_if_only_post_kickoff_rows_exist(tmp_path):
    ledger_path = tmp_path / "ledger.csv"
    kickoff = "2026-08-22T15:00:00+00:00"
    append_to_ledger([_pred_row("m1", "2026-08-23T00:00:00+00:00", kickoff, home_win=0.99)], ledger_path)

    ledger = read_ledger(ledger_path)
    with pytest.raises(ValueError, match="No pre-kickoff prediction"):
        select_pre_kickoff_predictions(ledger)


def test_select_pre_kickoff_predictions_restricts_to_requested_match_ids(tmp_path):
    ledger_path = tmp_path / "ledger.csv"
    append_to_ledger([
        _pred_row("m1", "2026-08-18T00:00:00+00:00", "2026-08-22T15:00:00+00:00"),
        _pred_row("m2", "2026-08-18T00:00:00+00:00", "2026-08-22T15:00:00+00:00"),
    ], ledger_path)
    ledger = read_ledger(ledger_path)
    selected = select_pre_kickoff_predictions(ledger, match_ids=["m1"])
    assert list(selected["match_id"]) == ["m1"]


def test_load_real_match_odds_only_uses_real_snapshot_rows(tmp_path):
    path = tmp_path / "match_odds.csv"
    pd.DataFrame([
        {"match_id": "m1", "data_status": "real_snapshot",
         "home_implied_probability_no_vig": 0.5, "draw_implied_probability_no_vig": 0.3, "away_implied_probability_no_vig": 0.2},
        {"match_id": "m2", "data_status": "unavailable",
         "home_implied_probability_no_vig": "", "draw_implied_probability_no_vig": "", "away_implied_probability_no_vig": ""},
    ]).to_csv(path, index=False)
    odds = load_real_match_odds(path)
    assert set(odds) == {"m1"}
    assert odds["m1"]["home_implied_probability_no_vig"] == 0.5


def test_load_live_match_odds_cleans_via_build_market_features(tmp_path):
    path = tmp_path / "real_odds.csv"
    pd.DataFrame([
        {"match_id": "m1", "is_real_data": True, "current_home_odds": 1.5, "current_draw_odds": 4.0, "current_away_odds": 6.0},
        {"match_id": "m2", "is_real_data": False, "current_home_odds": "", "current_draw_odds": "", "current_away_odds": ""},
    ]).to_csv(path, index=False)
    odds = load_live_match_odds(path)
    assert set(odds) == {"m1"}  # m2 has no real bookmaker rows -- never fabricated
    total = sum(odds["m1"].values())
    assert abs(total - 1.0) < 1e-6


def test_load_combined_match_odds_prefers_live_over_manual(tmp_path):
    real_odds_path = tmp_path / "real_odds.csv"
    match_odds_path = tmp_path / "match_odds.csv"
    # Live API has real data for m1 (should win); manual snapshot has a
    # DIFFERENT value for m1 (should be overridden) and the only data for m2.
    pd.DataFrame([
        {"match_id": "m1", "is_real_data": True, "current_home_odds": 1.5, "current_draw_odds": 4.0, "current_away_odds": 6.0},
    ]).to_csv(real_odds_path, index=False)
    pd.DataFrame([
        {"match_id": "m1", "data_status": "real_snapshot",
         "home_implied_probability_no_vig": 0.99, "draw_implied_probability_no_vig": 0.005, "away_implied_probability_no_vig": 0.005},
        {"match_id": "m2", "data_status": "real_snapshot",
         "home_implied_probability_no_vig": 0.4, "draw_implied_probability_no_vig": 0.3, "away_implied_probability_no_vig": 0.3},
    ]).to_csv(match_odds_path, index=False)

    combined = load_combined_match_odds(real_odds_path, match_odds_path)
    assert set(combined) == {"m1", "m2"}
    assert combined["m1"]["home_implied_probability_no_vig"] != 0.99  # live overrides manual
    assert combined["m2"]["home_implied_probability_no_vig"] == 0.4  # manual fills the gap live doesn't cover
