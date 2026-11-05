"""Markets' +2 Margin Survival equivalent: for every real instrument in
a market's universe, today's real P(this instrument's return over the
next real HORIZON_DAYS falls below a real, historically-derived
adverse threshold), bucketed into the same 5-tier shape every other
engine in this project uses (ELITE SURVIVAL / VERY STRONG / STRONG /
MODERATE / HIGH BLOWOUT RISK).

THRESHOLD and RISK_LABELS below are NOT guessed or borrowed from
soccer's/NFL's/NBA's own numbers, or from each other -- every single
market's own row here is that market's own real backtested value (see
each market's own reports/{market_id}_tail_risk_backtest_report.md,
all real-backtested 2026-11-05), hardcoded the same way
compute_margin_survival_team_sport.py hardcodes NFL/NBA/NCAA
Football's own real backtested MARGIN_THRESHOLD/RISK_LABELS -- re-run
a market's own backtest and update ITS OWN row if its real underlying
distribution moves meaningfully; never copy another market's numbers.

us_fixed_income_credit's THRESHOLD/RISK_LABELS are on a genuinely
different real scale from every other market here: FRED's `close` is
a yield/spread LEVEL (percentage points), not a price, so its
"return" is a real additive day-over-day level CHANGE (e.g. 0.12 means
a real 12-basis-point move), not a multiplicative log-return -- see
level_series() in backtest_market_tail_risk.py for why (DGS3MO hit a
real literal 0.00 on 21 real ZIRP-era days, which breaks a log
transform).

No directional (up/down) prediction anywhere in this module -- see
config/markets.yaml's docstring for why. This is a volatility/tail-
risk read only, built on a real, standard, zero-drift EWMA model, the
same one validated in the real backtest above (and re-fit here with
all real data available as of today, not frozen at backtest time).

Run: python -m src.models.compute_market_tail_risk --market us_equities
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_market_tail_risk import EWMA_LAMBDA, FREQUENCY_PARAMS, ewma_daily_vol, level_series  # noqa: E402
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

# Every market's own real backtested values (see this module's
# docstring and each market's own backtest report).
THRESHOLD = {
    "us_equities": 0.039697,
    "us_commodities": 0.045732,
    "us_fixed_income_credit": 0.12,  # real percentage-point yield/spread change, not a %-return -- see docstring
    "us_fx": 0.009928,
    "us_digital_assets": 0.071041,
    "us_real_assets": 0.029269,
    "us_alternatives": 0.009227,
    "india_equities": 0.034842,
    "india_fx": 0.009190,
    "india_digital_assets": 0.070946,
    "india_real_assets": 0.018188,
    "india_commodities": 0.030210,
    "india_fixed_income_credit": 0.172,  # real percentage-point yield change over 1 real month, not a %-return -- see docstring
}

RISK_LABELS = {
    "us_equities": [
        (0.0596, "ELITE SURVIVAL"), (0.1006, "VERY STRONG"), (0.1444, "STRONG"), (0.1984, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_commodities": [
        (0.0476, "ELITE SURVIVAL"), (0.1006, "VERY STRONG"), (0.1466, "STRONG"), (0.2158, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_fixed_income_credit": [
        (0.0156, "ELITE SURVIVAL"), (0.0950, "VERY STRONG"), (0.1626, "STRONG"), (0.2357, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_fx": [
        (0.0784, "ELITE SURVIVAL"), (0.1427, "VERY STRONG"), (0.1947, "STRONG"), (0.2442, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_digital_assets": [
        (0.0651, "ELITE SURVIVAL"), (0.1134, "VERY STRONG"), (0.1678, "STRONG"), (0.2140, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_real_assets": [
        (0.0699, "ELITE SURVIVAL"), (0.0971, "VERY STRONG"), (0.1287, "STRONG"), (0.1619, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "us_alternatives": [
        (0.0182, "ELITE SURVIVAL"), (0.1049, "VERY STRONG"), (0.2134, "STRONG"), (0.2865, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "india_equities": [
        (0.0778, "ELITE SURVIVAL"), (0.1131, "VERY STRONG"), (0.1471, "STRONG"), (0.1943, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "india_fx": [
        (0.0883, "ELITE SURVIVAL"), (0.1461, "VERY STRONG"), (0.2000, "STRONG"), (0.2495, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "india_digital_assets": [
        (0.0632, "ELITE SURVIVAL"), (0.1112, "VERY STRONG"), (0.1629, "STRONG"), (0.2113, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "india_real_assets": [
        (0.1542, "ELITE SURVIVAL"), (0.1975, "VERY STRONG"), (0.2239, "STRONG"), (0.2573, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    # Thinner real sample than every other market here (109 real
    # (ticker,checkpoint) pairs from only 2 tickers, vs. 171-1972
    # elsewhere) -- only 2 real liquid India commodity ETFs exist (see
    # markets.yaml), so the real backtested calibration is noisier
    # (non-monotonic across p_fail quintiles -- see this market's own
    # tail_risk_backtest_report.md). Disclosed honestly, not hidden or
    # padded with a fabricated third instrument.
    "india_commodities": [
        (0.0311, "ELITE SURVIVAL"), (0.1007, "VERY STRONG"), (0.1571, "STRONG"), (0.2128, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "india_fixed_income_credit": [
        (0.1334, "ELITE SURVIVAL"), (0.1758, "VERY STRONG"), (0.2147, "STRONG"), (0.2823, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
}

OUTPUT_COLUMNS = [
    "market_id", "ticker", "as_of_date", "current_price", "currency",
    "sigma_daily", "sigma_horizon", "horizon_days", "horizon_label", "threshold",
    "p_survive", "p_fail", "risk_label", "why_text",
    "run_id", "model_version", "generated_at",
]


def _risk_label(market_id: str, p_fail: float) -> str:
    for cutoff, label in RISK_LABELS[market_id]:
        if p_fail < cutoff:
            return label
    return RISK_LABELS[market_id][-1][1]


def _why_text(ticker: str, sigma_horizon: float, threshold: float, p_fail: float, is_fred: bool, horizon_label: str) -> str:
    unit = "percentage points of yield/spread" if is_fred else ""
    sigma_display = f"{sigma_horizon:.3f} {unit}".strip() if is_fred else f"{sigma_horizon:.2%}"
    threshold_display = f"{threshold:.3f} {unit}".strip() if is_fred else f"{threshold:.2%}"
    return (
        f"Real EWMA-fitted {horizon_label} volatility for {ticker}: {sigma_display} "
        f"(zero drift assumed -- this is a volatility read, not a directional call). "
        f"Net modeled probability of a real move worse than -{threshold_display} over the next "
        f"{horizon_label}: {p_fail:.1%}."
    )


def compute_for_market(market_id: str) -> pd.DataFrame:
    cfg = load_market_config(market_id)
    threshold = THRESHOLD[market_id]
    params = FREQUENCY_PARAMS[cfg.frequency]
    min_history, horizon = params["min_history"], params["horizon"]
    horizon_label = f"{horizon}-trading-day" if cfg.frequency == "daily" else f"{horizon}-month"
    horizon_short = f"{horizon}d" if cfg.frequency == "daily" else f"{horizon}mo"  # compact form for the site's own UI
    path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    df = pd.read_csv(path, parse_dates=["date"])

    meta = make_run_metadata(prefix="market_tail_risk", season="2026-27")
    generated_at = now_utc_iso()

    rows = []
    for ticker in cfg.tickers:
        t = df[df["ticker"] == ticker].sort_values("date").reset_index(drop=True)
        if len(t) < min_history:
            continue  # too thin a real history to fit a trustworthy EWMA vol -- skipped, not guessed
        diffs = np.diff(level_series(t["close"].values, cfg.source))
        sigma_period = ewma_daily_vol(diffs, lam=EWMA_LAMBDA)
        sigma_horizon = sigma_period * np.sqrt(horizon)
        p_fail = float(norm.cdf(-threshold, loc=0.0, scale=sigma_horizon))
        p_survive = 1 - p_fail
        label = _risk_label(market_id, p_fail)

        rows.append({
            "market_id": market_id, "ticker": ticker, "as_of_date": t["date"].iloc[-1].strftime("%Y-%m-%d"),
            "current_price": round(float(t["close"].iloc[-1]), 4), "currency": t["currency"].iloc[-1],
            "sigma_daily": round(sigma_period, 6), "sigma_horizon": round(sigma_horizon, 6),
            "horizon_days": horizon, "horizon_label": horizon_short, "threshold": round(threshold, 6),
            "p_survive": round(p_survive, 4), "p_fail": round(p_fail, 4), "risk_label": label,
            "why_text": _why_text(ticker, sigma_horizon, threshold, p_fail, is_fred=(cfg.source == "fred"), horizon_label=horizon_label),
            "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
        })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path = REPO_ROOT / "data" / "outputs" / market_path(market_id, "tail_risk.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    tally = out_df["risk_label"].value_counts().to_dict()
    print(f"Wrote {len(out_df)} tail-risk rows to {out_path} -- risk tiers: {tally}")
    log_experiment(meta, stage="compute_market_tail_risk", notes=f"{market_id}: {len(out_df)} rows, tiers={tally}")
    return out_df


def main(market_id: str) -> None:
    compute_for_market(market_id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
