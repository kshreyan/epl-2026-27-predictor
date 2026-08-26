"""Append-only pre-kickoff prediction ledger.

This closes a real gap: `data/outputs/epl_2026_27_match_predictions.csv`
is a single mutable file that gets read, patched, and rewritten every
time the weekly-update engine runs. It is careful not to overwrite a
completed match's own probability columns, but nothing enforces that,
and there is no durable record of what the model believed at each
point in time -- only the latest value survives.

Every prediction this pipeline ever generates for a match -- the
initial preseason run over all 380 fixtures, and every subsequent
weekly-update refresh for a still-not-yet-played fixture -- gets its
own permanent row here instead. Rows are written with a real file
*append* (`open(path, "a")`), never a read-the-whole-file-then-rewrite
cycle, so an existing row cannot be mutated by a later run even in
principle -- there is no code path that could do it. This is what
makes a later scoring pass trustworthy: the prediction scored for a
match is provably one that was generated before that match's own
kickoff, not silently regenerated after the fact from a model that has
since seen the result (see `select_pre_kickoff_predictions` below,
which enforces this as an assertion, not just a design intention).
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PRESEASON_TAG = "preseason-2026-27-v2"
PREDICTIONS_RELPATH = "data/outputs/epl_2026_27_match_predictions.csv"

LEDGER_COLUMNS = [
    "match_id", "matchweek", "home_team", "away_team", "kickoff_utc",
    "home_win_prob", "draw_prob", "away_win_prob",
    "dc_raw_home_win_prob", "dc_raw_draw_prob", "dc_raw_away_win_prob",
    "market_home_win_prob", "market_draw_prob", "market_away_win_prob", "market_available",
    "prediction_mode", "run_id", "model_version", "generated_at",
]


def prediction_rows_to_ledger_rows(pred_rows: list[dict], match_odds_by_id: dict | None = None) -> list[dict]:
    """Maps `predict_fixtures`' PREDICTION_COLUMNS-shaped dicts into the
    ledger's own (narrower, renamed) schema. `match_odds_by_id` (from
    `load_real_match_odds`) supplies the ledger's market_* fields when a
    real, manually-logged 1X2 snapshot exists for that match -- this is
    deliberately separate from PREDICTION_COLUMNS' own
    `*_market_integrated` fields, which represent a different, still-
    unbuilt blended model+market prediction feature. The ledger's
    market_* fields exist purely as a scoring BASELINE, not a feature."""
    match_odds_by_id = match_odds_by_id or {}
    rows = []
    for r in pred_rows:
        odds = match_odds_by_id.get(r["match_id"])
        if odds is not None:
            market_home, market_draw, market_away, market_available = (
                odds["home_implied_probability_no_vig"], odds["draw_implied_probability_no_vig"],
                odds["away_implied_probability_no_vig"], True,
            )
        else:
            market_home, market_draw, market_away, market_available = (
                r.get("home_win_prob_market_integrated", ""), r.get("draw_prob_market_integrated", ""),
                r.get("away_win_prob_market_integrated", ""), r.get("market_available", False),
            )
        rows.append({
            "match_id": r["match_id"], "matchweek": r["matchweek"],
            "home_team": r["home_team"], "away_team": r["away_team"],
            "kickoff_utc": r["kickoff_utc"],
            "home_win_prob": r["home_win_prob_model_only"],
            "draw_prob": r["draw_prob_model_only"],
            "away_win_prob": r["away_win_prob_model_only"],
            "dc_raw_home_win_prob": r["dc_raw_home_win_prob"],
            "dc_raw_draw_prob": r["dc_raw_draw_prob"],
            "dc_raw_away_win_prob": r["dc_raw_away_win_prob"],
            "market_home_win_prob": market_home, "market_draw_prob": market_draw, "market_away_win_prob": market_away,
            "market_available": market_available,
            "prediction_mode": r["prediction_mode"], "run_id": r["run_id"],
            "model_version": r["model_version"], "generated_at": r["generated_at"],
        })
    return rows


def load_real_match_odds(match_odds_path: Path) -> dict:
    """Real, manually-logged match_id -> de-vigged 1X2 probability dict,
    from `data/raw/epl_2026_27_match_odds.csv`'s `real_snapshot` rows
    only (sentinel `unavailable` rows are never used). One bookmaker per
    match, entered by hand -- see `load_live_match_odds` for the richer,
    multi-bookmaker live-API source, which takes priority when both are
    available (see `load_combined_match_odds`)."""
    if not match_odds_path.exists():
        return {}
    df = pd.read_csv(match_odds_path)
    real = df[df["data_status"] == "real_snapshot"]
    return {
        row["match_id"]: {
            "home_implied_probability_no_vig": row["home_implied_probability_no_vig"],
            "draw_implied_probability_no_vig": row["draw_implied_probability_no_vig"],
            "away_implied_probability_no_vig": row["away_implied_probability_no_vig"],
        }
        for _, row in real.iterrows()
    }


def load_live_match_odds(real_odds_path: Path) -> dict:
    """Real match_id -> de-vigged 1X2 probability dict from the live
    The Odds API feed (`data/raw/epl_2026_27_real_odds.csv`, written by
    `collect_odds.py` when `ODDS_API_KEY` is configured), cleaned via
    `build_market_features`'s real, unit-tested overround-removal and
    cross-bookmaker log-odds averaging -- typically 15-20+ real
    bookmakers per fixture once a market is posted, not the single
    manually-entered price `load_real_match_odds` reads."""
    if not real_odds_path.exists():
        return {}
    from src.features.build_market_features import build_market_features
    odds_df = pd.read_csv(real_odds_path)
    market_df = build_market_features(odds_df)
    available = market_df[market_df["market_available"] == True]  # noqa: E712
    return {
        row["match_id"]: {
            "home_implied_probability_no_vig": row["market_home_win_prob_current"],
            "draw_implied_probability_no_vig": row["market_draw_prob_current"],
            "away_implied_probability_no_vig": row["market_away_win_prob_current"],
        }
        for _, row in available.iterrows()
    }


def load_live_spread_totals_odds(real_odds_path: Path) -> dict:
    """Real match_id -> {"spread_line", "home_cover_prob", "total_line",
    "over_prob"} dict from the live Odds API feed's "spreads"/"totals"
    market rows (data/raw/epl_2026_27_real_odds.csv), for use by the
    validated spread/totals model+market blends
    (spread_totals_blend_model.py). A fixture may have only one of the
    two markets covered (bookmakers post them independently) -- the
    dict only includes the keys that market actually has real data for.

    Different bookmakers can quote different handicap/total lines for
    the same fixture; this uses the modal (most commonly quoted) line
    and averages, in logit space, only the bookmakers quoting that
    exact line -- the same "don't average across different bets"
    principle real odds-comparison sites use, rather than blending
    probabilities that refer to different lines."""
    if not real_odds_path.exists():
        return {}
    from src.features.build_market_features import log_odds_average_binary, remove_overround_binary
    odds_df = pd.read_csv(real_odds_path)
    result: dict = {}
    for match_id, group in odds_df.groupby("match_id"):
        entry = {}

        spreads = group[(group["market_type"] == "spreads") & (group["is_real_data"] == True)]  # noqa: E712
        if not spreads.empty:
            modal_line = spreads["spread_line"].mode().iloc[0]
            at_line = spreads[spreads["spread_line"] == modal_line]
            cover_probs = [
                remove_overround_binary((float(r["home_spread_odds"]), float(r["away_spread_odds"])))[0]
                for _, r in at_line.iterrows()
            ]
            entry["spread_line"] = float(modal_line)
            entry["home_cover_prob"] = log_odds_average_binary(cover_probs)

        totals = group[(group["market_type"] == "totals") & (group["is_real_data"] == True)]  # noqa: E712
        if not totals.empty:
            modal_line = totals["total_line"].mode().iloc[0]
            at_line = totals[totals["total_line"] == modal_line]
            over_probs = [
                remove_overround_binary((float(r["over_odds"]), float(r["under_odds"])))[0]
                for _, r in at_line.iterrows()
            ]
            entry["total_line"] = float(modal_line)
            entry["over_prob"] = log_odds_average_binary(over_probs)

        if entry:
            result[match_id] = entry
    return result


def load_combined_match_odds(real_odds_path: Path, match_odds_path: Path) -> dict:
    """Live multi-bookmaker API odds where available, falling back to the
    single-bookmaker manual snapshot for any match the live feed hasn't
    posted a market for yet (bookmakers only post EPL markets shortly
    before kickoff, so most of the season is covered by neither at any
    given time -- that stays honestly reflected as market_available=False
    downstream, not proxied)."""
    manual = load_real_match_odds(match_odds_path)
    live = load_live_match_odds(real_odds_path)
    return {**manual, **live}  # live overrides manual for any match_id in both


def append_to_ledger(pred_rows: list[dict], ledger_path: Path, match_odds_by_id: dict | None = None) -> None:
    """Appends one row per prediction to `ledger_path`, creating it with
    a header the first time. Pure append -- never reads the file back in
    to rewrite it, so no existing row can be touched."""
    if not pred_rows:
        return
    ledger_rows = prediction_rows_to_ledger_rows(pred_rows, match_odds_by_id=match_odds_by_id)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not ledger_path.exists()
    with open(ledger_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        if write_header:
            writer.writeheader()
        for row in ledger_rows:
            writer.writerow({col: row.get(col, "") for col in LEDGER_COLUMNS})


def read_ledger(ledger_path: Path) -> pd.DataFrame:
    if not ledger_path.exists():
        return pd.DataFrame(columns=LEDGER_COLUMNS)
    df = pd.read_csv(ledger_path)
    df["kickoff_utc"] = pd.to_datetime(df["kickoff_utc"], utc=True)
    df["generated_at"] = pd.to_datetime(df["generated_at"], utc=True)
    return df


def select_pre_kickoff_predictions(ledger: pd.DataFrame, match_ids: list | None = None) -> pd.DataFrame:
    """For each match_id (optionally restricted to `match_ids`), returns
    the single most-recent ledger row whose generated_at is strictly
    before that match's own kickoff_utc -- the prediction a forecaster
    genuinely held right before kickoff.

    Raises if any requested match_id has zero such rows (every
    prediction ever logged for it came at or after kickoff -- a real
    problem, never silently skipped). Asserts, for the rows actually
    returned, that generated_at < kickoff_utc -- the leak-check, made
    operational rather than just reasoned about.
    """
    if match_ids is not None:
        ledger = ledger[ledger["match_id"].isin(match_ids)]

    valid = ledger[ledger["generated_at"] < ledger["kickoff_utc"]] if not ledger.empty else ledger
    requested = set(match_ids) if match_ids is not None else set(ledger["match_id"])
    missing = requested - set(valid["match_id"])
    if missing:
        raise ValueError(
            f"No pre-kickoff prediction exists for match_id(s) {missing} -- every "
            "ledger row logged for these matches was generated at or after kickoff, "
            "so none of them can be honestly scored."
        )

    idx = valid.groupby("match_id")["generated_at"].idxmax()
    selected = valid.loc[idx].reset_index(drop=True)
    assert (selected["generated_at"] < selected["kickoff_utc"]).all(), (
        "leak-check failed: a row selected for scoring is not actually pre-kickoff"
    )
    return selected


def load_preseason_ledger(
    git_ref: str = PRESEASON_TAG, repo_root: Path = REPO_ROOT, predictions_relpath: str = PREDICTIONS_RELPATH,
) -> pd.DataFrame:
    """The frozen `preseason-2026-27-v2` forecast, read directly from its
    git tag rather than from the live ledger -- the ledger itself did
    not exist yet as of that tag (it was added in a later commit), so
    this is the only way to recover exactly what was locked at kickoff-3
    without relying on the ledger's first block happening to match
    (true today only by coincidence, not by any enforced invariant).

    The tagged `epl_2026_27_match_predictions.csv` has no dc_raw_*
    columns (added after v2 was tagged) -- those are set to NaN here,
    honestly, rather than backfilled from a model refit today, which
    would not reflect what was actually computed at tag time and would
    reintroduce exactly the leak this whole module exists to prevent.
    Scoring against this track therefore has NO Dixon-Coles-raw
    baseline available; only the production probabilities can be
    scored against it.
    """
    result = subprocess.run(
        ["git", "show", f"{git_ref}:{predictions_relpath}"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    from io import StringIO
    tagged = pd.read_csv(StringIO(result.stdout))

    ledger_shaped = pd.DataFrame({
        "match_id": tagged["match_id"], "matchweek": tagged["matchweek"],
        "home_team": tagged["home_team"], "away_team": tagged["away_team"],
        "kickoff_utc": tagged["kickoff_utc"],
        "home_win_prob": tagged["home_win_prob_model_only"],
        "draw_prob": tagged["draw_prob_model_only"],
        "away_win_prob": tagged["away_win_prob_model_only"],
        "dc_raw_home_win_prob": pd.NA, "dc_raw_draw_prob": pd.NA, "dc_raw_away_win_prob": pd.NA,
        "market_home_win_prob": pd.NA, "market_draw_prob": pd.NA, "market_away_win_prob": pd.NA,
        "market_available": False,
        "prediction_mode": tagged["prediction_mode"], "run_id": tagged["run_id"],
        "model_version": tagged["model_version"], "generated_at": tagged["generated_at"],
    })
    ledger_shaped["kickoff_utc"] = pd.to_datetime(ledger_shaped["kickoff_utc"], utc=True)
    ledger_shaped["generated_at"] = pd.to_datetime(ledger_shaped["generated_at"], utc=True)
    return ledger_shaped
