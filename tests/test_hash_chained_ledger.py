"""Tests the hash-chained prediction ledger: each row's hash must
depend on the real content of every row before it, so altering or
deleting a historical row is detectable, not just append-only by
convention."""
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.hash_chained_ledger import (  # noqa: E402
    GENESIS_HASH,
    ROW_FIELDS,
    _db_path,
    append_prediction,
    compute_row_hash,
    verify_chain,
)

TEST_LEAGUE = "test_hash_chain_league"


@pytest.fixture(autouse=True)
def _clean_test_ledger():
    path = _db_path(TEST_LEAGUE)
    if path.exists():
        path.unlink()
    yield
    if path.exists():
        path.unlink()


def _row(match_id: str, **overrides) -> dict:
    base = {
        "match_id": match_id, "kickoff_utc": "2026-11-01T18:00:00+00:00",
        "prediction_timestamp": "2026-10-28T12:00:00+00:00",
        "model_version": "0.1.0-phase1", "model_home_win_prob": 0.55,
        "model_away_win_prob": 0.45,
    }
    base.update(overrides)
    return base


def test_first_row_chains_from_genesis():
    verify_chain(TEST_LEAGUE)  # vacuous, no file yet
    append_prediction(TEST_LEAGUE, _row("GAME_1"))
    conn = sqlite3.connect(_db_path(TEST_LEAGUE))
    prev_hash = conn.execute("SELECT prev_hash FROM predictions WHERE id = 1").fetchone()[0]
    conn.close()
    assert prev_hash == GENESIS_HASH


def test_append_prediction_requires_required_fields():
    with pytest.raises(ValueError):
        append_prediction(TEST_LEAGUE, {"match_id": "GAME_1"})  # missing prediction_timestamp


def test_chain_verifies_clean_after_several_appends():
    for i in range(5):
        append_prediction(TEST_LEAGUE, _row(f"GAME_{i}"))
    result = verify_chain(TEST_LEAGUE)
    assert result.ok
    assert result.n_rows == 5
    assert result.first_break_id is None


def test_tampering_with_a_historical_row_breaks_the_chain():
    for i in range(3):
        append_prediction(TEST_LEAGUE, _row(f"GAME_{i}"))
    conn = sqlite3.connect(_db_path(TEST_LEAGUE))
    conn.execute("UPDATE predictions SET model_home_win_prob = ? WHERE id = 1", ["0.99"])
    conn.commit()
    conn.close()

    result = verify_chain(TEST_LEAGUE)
    assert not result.ok
    assert result.first_break_id == 1


def test_deleting_a_historical_row_breaks_the_chain():
    for i in range(3):
        append_prediction(TEST_LEAGUE, _row(f"GAME_{i}"))
    conn = sqlite3.connect(_db_path(TEST_LEAGUE))
    conn.execute("DELETE FROM predictions WHERE id = 2")
    conn.commit()
    conn.close()

    result = verify_chain(TEST_LEAGUE)
    assert not result.ok
    assert result.first_break_id == 3  # row 3's prev_hash no longer matches row 1's (row 2 is gone)


def test_compute_row_hash_is_deterministic_and_order_independent():
    row_a = {"match_id": "X", "model_home_win_prob": 0.6}
    row_b = {"model_home_win_prob": 0.6, "match_id": "X"}  # same content, different key order
    assert compute_row_hash("abc", row_a) == compute_row_hash("abc", row_b)


def test_compute_row_hash_changes_with_prev_hash():
    row = {"match_id": "X", "model_home_win_prob": 0.6}
    assert compute_row_hash("abc", row) != compute_row_hash("def", row)


def test_chain_verifies_clean_with_long_float_probabilities():
    # Round literals like 0.55 happen to format identically whether
    # Python's str() or SQLite's own REAL-to-TEXT conversion produces
    # the stored bytes -- a real model-computed probability (many
    # significant digits) does NOT, which is exactly the real bug this
    # regression test catches (see append_prediction's _stringify_row
    # fix): hashing against the stringified value but inserting the
    # raw float let SQLite's own formatting silently diverge from what
    # was hashed, failing re-verification on a perfectly untampered row.
    append_prediction(TEST_LEAGUE, _row("GAME_1", model_home_win_prob=0.5537291834728193))
    result = verify_chain(TEST_LEAGUE)
    assert result.ok


def test_row_fields_never_silently_drops_a_supplied_value():
    append_prediction(TEST_LEAGUE, _row("GAME_1", market_home_win_prob=0.5, blended_home_win_prob=0.52))
    conn = sqlite3.connect(_db_path(TEST_LEAGUE))
    stored = dict(zip(["id", "prev_hash", "row_hash", "inserted_at", *ROW_FIELDS],
                       conn.execute("SELECT * FROM predictions WHERE id = 1").fetchone()))
    conn.close()
    assert stored["market_home_win_prob"] == "0.5"
    assert stored["blended_home_win_prob"] == "0.52"
