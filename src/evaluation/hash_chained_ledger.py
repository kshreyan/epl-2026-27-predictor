"""Append-only, hash-chained prediction ledger (SQLite + sha256, both
stdlib -- no new dependency).

This is a stricter sibling of `prediction_ledger.py` (the existing CSV
append-only ledger soccer/the continental cups use): same leak-safe
"predictions written before kickoff, results joined after" discipline,
but with each row's hash depending on the previous row's hash, so
tampering with or deleting any historical row breaks every row after
it in a way `verify_chain()` below detects deterministically. Reused
across every sport this phase and beyond (not duplicated per sport) --
callers pass their own `league_id`/`match_id`/probabilities; this
module has no sport-specific logic.

Every row stores the model probability, the market probability, and
the model+market blended probability as three SEPARATE column groups
(never conflated into one "probability" field) -- the same discipline
`prediction_ledger.py`'s own market_* columns already established,
generalized here to also carry the blended figure.

Run: python -m src.evaluation.hash_chained_ledger --verify --league nfl
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.leagues import league_path  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
GENESIS_HASH = "0" * 64

# Every column a row can carry (nullable ones stay None for a sport/
# call that has no real value for them -- e.g. draw_prob for a sport
# with no real tie outcome, or margin_quantiles_json for a model with
# no real margin distribution).
ROW_FIELDS = [
    "league_id", "match_id", "kickoff_utc", "prediction_timestamp",
    "model_version", "git_sha", "data_snapshot_hash", "features_hash",
    "model_home_win_prob", "model_draw_prob", "model_away_win_prob",
    "market_home_win_prob", "market_draw_prob", "market_away_win_prob",
    "blended_home_win_prob", "blended_draw_prob", "blended_away_win_prob",
    "margin_quantiles_json", "total_quantiles_json",
    "odds_snapshot_id", "run_id",
]


def _db_path(league_id: str) -> Path:
    return REPO_ROOT / "data" / "outputs" / league_path(league_id, "prediction_ledger.sqlite3")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prev_hash TEXT NOT NULL,
            row_hash TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            {", ".join(f"{col} TEXT" for col in ROW_FIELDS)}
        )
    """)
    return conn


def _stringify_row(row: dict) -> dict:
    """Every ledger column is stored as SQLite TEXT, which coerces any
    inserted non-string value (a float, an int) to its string form --
    reading it back later therefore never returns the original Python
    type. Hashing must use the SAME stringified form at both append
    time and verify time, or a perfectly untampered row would fail
    re-verification purely from a float-vs-string type mismatch (the
    real bug this fixes, caught by this module's own tests). None
    stays None (SQLite NULL), everything else becomes str(v)."""
    return {k: (None if v is None else str(v)) for k, v in row.items()}


def _canonical_json(row: dict) -> str:
    """Deterministic serialization (sorted keys, no whitespace
    ambiguity) -- the same row content must always hash the same way,
    independent of dict insertion order."""
    return json.dumps(_stringify_row(row), sort_keys=True, separators=(",", ":"))


def compute_row_hash(prev_hash: str, row: dict) -> str:
    payload = f"{prev_hash}|{_canonical_json(row)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_prediction(league_id: str, row: dict) -> str:
    """Appends one real pre-kickoff prediction row, chained to the
    current last row's hash (or GENESIS_HASH for the first row in this
    league's ledger). Returns the new row's hash. `row` must supply
    every key in ROW_FIELDS it has a real value for; missing keys are
    stored as null, never fabricated."""
    missing_required = {"match_id", "prediction_timestamp"} - set(row)
    if missing_required:
        raise ValueError(f"append_prediction: missing required field(s) {missing_required}")

    db_path = _db_path(league_id)
    conn = _connect(db_path)
    try:
        cur = conn.execute("SELECT row_hash FROM predictions ORDER BY id DESC LIMIT 1")
        last = cur.fetchone()
        prev_hash = last[0] if last else GENESIS_HASH

        full_row = {col: row.get(col) for col in ROW_FIELDS}
        full_row["league_id"] = league_id
        row_hash = compute_row_hash(prev_hash, full_row)

        # Insert the SAME stringified values the hash was computed over
        # (not the raw Python/numpy objects) -- every column is TEXT, so
        # letting sqlite3/SQLite do its own numeric-to-text conversion on
        # a raw float/np.float64 can produce different bytes than
        # Python's own str(v) did for hashing, which would make a
        # perfectly untampered row fail its own re-verification purely
        # from a representation mismatch (the real bug this fixes,
        # caught by this module's own tests).
        stored_row = _stringify_row(full_row)
        import datetime
        inserted_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        placeholders = ", ".join(["?"] * (len(ROW_FIELDS) + 3))
        cols = ", ".join(["prev_hash", "row_hash", "inserted_at", *ROW_FIELDS])
        conn.execute(
            f"INSERT INTO predictions ({cols}) VALUES ({placeholders})",
            [prev_hash, row_hash, inserted_at, *[stored_row[c] for c in ROW_FIELDS]],
        )
        conn.commit()
        return row_hash
    finally:
        conn.close()


@dataclass
class ChainVerificationResult:
    ok: bool
    n_rows: int
    first_break_id: int | None
    detail: str


def verify_chain(league_id: str) -> ChainVerificationResult:
    """Walks every row in insertion order and recomputes its hash from
    its own stored content + the previous row's stored hash -- a
    mismatch anywhere (a row's content was altered, a row was deleted,
    or a row's prev_hash doesn't match the row before it) is reported
    at the FIRST broken id, not silently averaged away."""
    db_path = _db_path(league_id)
    if not db_path.exists():
        return ChainVerificationResult(ok=True, n_rows=0, first_break_id=None, detail="no ledger file yet -- vacuously valid")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            f"SELECT id, prev_hash, row_hash, {', '.join(ROW_FIELDS)} FROM predictions ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()

    expected_prev = GENESIS_HASH
    for r in rows:
        row_id, stored_prev_hash, stored_row_hash = r[0], r[1], r[2]
        field_values = dict(zip(ROW_FIELDS, r[3:]))
        if stored_prev_hash != expected_prev:
            return ChainVerificationResult(
                ok=False, n_rows=len(rows), first_break_id=row_id,
                detail=f"row {row_id}'s stored prev_hash does not match row {row_id - 1}'s real row_hash",
            )
        recomputed = compute_row_hash(stored_prev_hash, field_values)
        if recomputed != stored_row_hash:
            return ChainVerificationResult(
                ok=False, n_rows=len(rows), first_break_id=row_id,
                detail=f"row {row_id}'s content does not hash to its own stored row_hash -- altered after insert",
            )
        expected_prev = stored_row_hash

    return ChainVerificationResult(ok=True, n_rows=len(rows), first_break_id=None, detail="chain intact")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, dest="league_id")
    _parser.add_argument("--verify", action="store_true")
    _args = _parser.parse_args()
    if _args.verify:
        result = verify_chain(_args.league_id)
        print(f"{_args.league_id}: {result.n_rows} row(s) -- {'OK' if result.ok else 'BROKEN'}: {result.detail}")
        sys.exit(0 if result.ok else 1)
