"""One-off repair of completed domestic-league rows locked BEFORE the
market-blend mislabeling fix (commit 1b4467f, 2026-11-19).

Before that fix, predict_all_matches.predict_fixtures overwrote the
model's own calibrated 1X2 probability with the model+market blend, then
wrote the blended value into the *_model_only columns, left every
*_market_integrated column blank, and hardcoded market_available=False.
Rows already locked as completed were deliberately left untouched by
that fix, so they still carry the mislabel: market_blend_applied=True
but market_available=False, with blended numbers under *_model_only.

What this script does, per affected row (and nothing else):

1. Moves the blended 1X2 probabilities into the *_market_integrated
   columns, where they belong.
2. Sets market_available=True. A blend is only ever applied when real
   odds exist for that fixture, so this is a fact, not a guess.
3. Recovers the true model-only 1X2 probabilities by inverting the blend.
   The blend is `log_odds_average([model, market])`: a per-class mean of
   logits, then renormalised. Given the stored blend b and the exact
   market triple k recorded in that league's prediction ledger under the
   same run_id, model m solves sigmoid((logit(m_i) + logit(k_i)) / 2) = Z*b_i
   with sum(m) = 1, a one-dimensional root-find in Z. Every recovered
   triple is checked by re-blending it with k and requiring the result
   to match the stored b to within 4-decimal rounding (ROUND_TRIP_TOL).
4. If the ledger has no row for that (match_id, run_id), the market
   triple is unknown and the model-only value cannot be recovered. Those
   *_model_only 1X2 columns are blanked rather than guessed, and
   downstream readers already skip blank probabilities.

Completed-match results, scorelines, BTTS/totals/spread columns,
confidence, picks and every scheduled row are left exactly as they are.
Idempotent: a repaired row no longer matches the selection condition.

Run: python scripts/repair_pre_fix_blend_labels.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from src.features.build_market_features import log_odds_average  # noqa: E402

OUT = REPO_ROOT / "data" / "outputs"
DOMESTIC_LEAGUES = ["epl", "la_liga", "serie_a", "bundesliga", "ligue_1"]
OUTCOMES = ["home_win", "draw", "away_win"]
MODEL_COLS = ["home_win_prob_model_only", "draw_prob_model_only", "away_win_prob_model_only"]
MARKET_COLS = ["home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated"]
LEDGER_BLEND_COLS = ["home_win_prob", "draw_prob", "away_win_prob"]
LEDGER_MARKET_COLS = ["market_home_win_prob", "market_draw_prob", "market_away_win_prob"]
ROUND_TRIP_TOL = 2e-4  # both b and k are stored at 4 decimals
EPS = 1e-12


def _logit(p: np.ndarray) -> np.ndarray:
    return np.log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def invert_blend(blend: list[float], market: list[float]) -> np.ndarray:
    """Model triple m such that log_odds_average([m, market]) == blend.

    A class with b_i == 0 can only come from a model probability of
    exactly 0 (the logit average sends any -inf input to 0 whatever the
    market says). Isotonic calibration does emit exact 0s for long-shot
    outcomes, so that class correctly inverts to m_i == 0; the
    divide-by-zero inside log() on that path is expected and silenced.
    """
    b, k = np.asarray(blend, float), np.asarray(market, float)

    def excess(z: float) -> float:
        zb = np.clip(z * b, EPS, 1.0 - EPS)
        return float(_sigmoid(2.0 * _logit(zb) - _logit(k)).sum() - 1.0)

    with np.errstate(divide="ignore"):
        z = brentq(excess, EPS, (1.0 - EPS) / b.max())
        m = _sigmoid(2.0 * _logit(z * b) - _logit(k))
    return m / m.sum()


def _fmt(v: float) -> str:
    """Same text pandas writes for a 4-decimal float (0.5 -> "0.5", 0 -> "0.0")."""
    return repr(round(float(v), 4))


def repair_league(league: str, dry_run: bool) -> dict:
    preds_path = OUT / f"{league}_2026_27_match_predictions.csv"
    ledger_path = OUT / f"{league}_2026_27_prediction_ledger.csv"
    # Read every cell as its original text so rows this script doesn't
    # touch are written back byte-for-byte (a plain read_csv round-trip
    # rewrites e.g. goals "3" as "3.0" on every completed row).
    preds = pd.read_csv(preds_path, dtype=str, keep_default_na=False)
    ledger = pd.read_csv(ledger_path)
    ledger_by_key = ledger.set_index(["match_id", "run_id"])

    affected = preds.index[(preds["market_blend_applied"] == "True") & (preds["market_available"] == "False")]
    recovered = blanked = 0
    max_err = 0.0

    for idx in affected:
        row = preds.loc[idx]
        if row["status"] != "completed":
            raise RuntimeError(f"{league}: {row['match_id']} is affected but not completed -- refusing to touch it")
        blend = [float(row[c]) for c in MODEL_COLS]

        for mc in MARKET_COLS:
            preds.at[idx, mc] = row[mc.replace("_market_integrated", "_model_only")]
        preds.at[idx, "market_available"] = "True"

        key = (row["match_id"], row["run_id"])
        model_only = None
        if key in ledger_by_key.index:
            lrow = ledger_by_key.loc[key]
            ledger_blend = [float(lrow[c]) for c in LEDGER_BLEND_COLS]
            market = [float(lrow[c]) for c in LEDGER_MARKET_COLS]
            if np.allclose(ledger_blend, blend, atol=1e-6) and not any(np.isnan(market)):
                m = invert_blend(blend, market)
                err = float(np.abs(np.array(log_odds_average([tuple(m), tuple(market)])) - np.array(blend)).max())
                if err <= ROUND_TRIP_TOL:
                    model_only = m
                    max_err = max(max_err, err)

        if model_only is not None:
            for mc, v in zip(MODEL_COLS, model_only):
                preds.at[idx, mc] = _fmt(v)
            recovered += 1
        else:
            for mc in MODEL_COLS:
                preds.at[idx, mc] = ""
            blanked += 1

    if len(affected) and not dry_run:
        preds.to_csv(preds_path, index=False)
    return {"league": league, "affected": len(affected), "recovered": recovered,
            "blanked": blanked, "max_round_trip_err": max_err}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for league in DOMESTIC_LEAGUES:
        r = repair_league(league, args.dry_run)
        print(f"{r['league']:11s} affected={r['affected']:3d} recovered={r['recovered']:3d} "
              f"blanked (no ledger entry)={r['blanked']:2d} max round-trip err={r['max_round_trip_err']:.1e}"
              f"{' [dry run]' if args.dry_run else ''}")


if __name__ == "__main__":
    main()
