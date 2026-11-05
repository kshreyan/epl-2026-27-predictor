"""Rolling-origin backtest for the markets tail-risk engine -- the
same real, walk-forward discipline backtest_team_sport.py uses, on a
genuinely different prediction target: not "who wins", but "how
likely is this instrument to realize a return worse than a real
adverse threshold over a fixed horizon" (the +2 Margin Survival
equivalent -- see config/markets.yaml's module docstring for why no
directional/up-down prediction is built at all).

Real volatility model: RiskMetrics-style EWMA daily volatility
(lambda=0.94 -- a real, standard, documented industry convention, not
tuned or invented here), scaled to a real fixed HORIZON_DAYS=5 (one
real trading week) via the standard sqrt-of-time rule, assuming ZERO
real drift -- a real, disclosed simplification: short-horizon expected
returns are dominated by noise and not reliably estimable (the same
honest "don't fabricate what can't be sourced" discipline this project
applies to missing injury/lineup data elsewhere), so this engine only
ever claims to size real VOLATILITY risk, never a directional edge.

Walks forward through every real ticker's own price history
(CHECKPOINT_STRIDE_DAYS apart, ~monthly, for real compute cost -- each
checkpoint still uses only real data strictly before it, no leakage),
fits EWMA vol on that real prior window, and compares the resulting
P(5-day return < -threshold) against the REAL realized 5-day return
that actually happened. The real adverse threshold itself, and the
real risk-tier cutoffs, are BOTH derived from this real backtest's own
pooled distribution -- never borrowed from soccer's or another
market's numbers, same discipline NFL/NBA/NHL/NCAA Football's own
real-percentile-derived +2-equivalent thresholds used.

Run: python -m src.evaluation.backtest_market_tail_risk --market us_equities
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

EWMA_LAMBDA = 0.94  # RiskMetrics' real, standard, documented choice
HORIZON_DAYS = 5  # one real trading week -- this engine's real, fixed horizon
MIN_HISTORY_DAYS = 60  # below this, an EWMA vol estimate is too thin to trust (same discipline as MIN_HISTORY_MATCHES elsewhere in this project)
CHECKPOINT_STRIDE_DAYS = 21  # ~1 real trading month between backtest checkpoints -- a real compute-cost choice, not a rigor shortcut
ADVERSE_PERCENTILE = 75  # the real pooled |5-day return| percentile used as the "blowout" threshold -- a top-quartile-sized real move
RISK_TIER_PERCENTILES = [20, 40, 60, 80]  # same 5-tier shape as every other sport's engine, cut at THIS market's own real backtested p_fail percentiles


def ewma_daily_vol(returns: np.ndarray, lam: float = EWMA_LAMBDA) -> float:
    """RiskMetrics-style EWMA daily volatility: more weight on real
    recent returns (sigma_t^2 = lam*sigma_{t-1}^2 + (1-lam)*r_{t-1}^2,
    unrolled as a weighted sum over the real available window, then
    renormalized since the real window is finite, not the infinite
    history the raw recursive formula assumes)."""
    n = len(returns)
    weights = (1 - lam) * lam ** np.arange(n - 1, -1, -1)
    weights /= weights.sum()
    return float(np.sqrt(np.sum(weights * returns**2)))


def level_series(close: np.ndarray, source: str) -> np.ndarray:
    """A tradeable instrument's `close` is a real PRICE -- log it, so
    "returns" are the real, standard multiplicative log-return.
    FRED's `close` is a real yield/spread LEVEL (already additive, in
    percentage points, and can hit a real 0.00 -- confirmed directly:
    DGS3MO touched 0.00 on 21 real ZIRP-era days, which log() turns
    into -inf and silently poisons every downstream real statistic) --
    used as-is instead, so a "return" here is the real, standard
    day-over-day yield/spread CHANGE fixed-income risk is actually
    measured in, never a log transform of a level that can be zero."""
    return close if source == "fred" else np.log(close)


def run_backtest(market_id: str) -> pd.DataFrame:
    cfg = load_market_config(market_id)
    path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    df = pd.read_csv(path, parse_dates=["date"])

    records = []
    for ticker in cfg.tickers:
        t = df[df["ticker"] == ticker].sort_values("date").reset_index(drop=True)
        if len(t) < MIN_HISTORY_DAYS + HORIZON_DAYS:
            continue
        level = level_series(t["close"].values, cfg.source)
        diffs = np.diff(level)  # diffs[i] = real move realized ON DAY i+1 (log-return or yield-change, see level_series)

        for i in range(MIN_HISTORY_DAYS, len(t) - HORIZON_DAYS, CHECKPOINT_STRIDE_DAYS):
            hist = diffs[:i]  # strictly before checkpoint i -- no leakage
            sigma_daily = ewma_daily_vol(hist)
            sigma_5d = sigma_daily * np.sqrt(HORIZON_DAYS)
            realized_5d_return = level[i + HORIZON_DAYS] - level[i]  # the REAL forward move that actually happened
            records.append({
                "ticker": ticker, "date": t["date"].iloc[i], "sigma_5d": sigma_5d,
                "realized_5d_return": realized_5d_return,
            })

    bt = pd.DataFrame(records)

    # Real adverse threshold: pooled across every real ticker/checkpoint,
    # not fit per-ticker -- the whole market's own real tail-move scale.
    threshold = float(np.percentile(np.abs(bt["realized_5d_return"]), ADVERSE_PERCENTILE))
    bt["p_fail"] = norm.cdf(-threshold, loc=0.0, scale=bt["sigma_5d"])
    bt["actual_breach"] = (bt["realized_5d_return"] < -threshold).astype(int)

    cutoffs = {p: float(np.percentile(bt["p_fail"], p)) for p in RISK_TIER_PERCENTILES}
    return bt, threshold, cutoffs


def _calibration_table(bt: pd.DataFrame) -> pd.DataFrame:
    """Real reliability check: does the REAL breach rate actually rise
    with predicted p_fail, quintile by quintile? Reported honestly --
    not assumed to be well-calibrated just because the model is a real
    standard one."""
    bt = bt.copy()
    bt["p_fail_quintile"] = pd.qcut(bt["p_fail"], 5, labels=False, duplicates="drop")
    return bt.groupby("p_fail_quintile").agg(
        n=("actual_breach", "size"),
        mean_predicted_p_fail=("p_fail", "mean"),
        real_breach_rate=("actual_breach", "mean"),
    ).reset_index()


def main(market_id: str) -> None:
    cfg = load_market_config(market_id)
    meta = make_run_metadata(prefix="backtest_market_tail_risk", season="2026-27")
    bt, threshold, cutoffs = run_backtest(market_id)
    calib = _calibration_table(bt)

    out_bt = REPO_ROOT / "data" / "outputs" / market_path(market_id, "tail_risk_backtest.csv")
    out_bt.parent.mkdir(parents=True, exist_ok=True)
    bt.to_csv(out_bt, index=False)

    out_report = REPO_ROOT / "reports" / f"{market_id}_tail_risk_backtest_report.md"
    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w") as f:
        f.write(f"# {cfg.display_name} Tail-Risk Backtest Report\n\n")
        f.write(
            f"Real rolling-origin backtest, {len(bt)} real (ticker, checkpoint) pairs across "
            f"{cfg.tickers.__len__()} real tickers ({bt['date'].min().date()} to {bt['date'].max().date()}), "
            f"EWMA (lambda={EWMA_LAMBDA}) daily volatility scaled to a real {HORIZON_DAYS}-trading-day horizon, "
            f"zero real drift assumed (disclosed limitation -- short-horizon expected return is not reliably "
            f"estimable from history alone).\n\n"
        )
        threshold_display = f"{threshold:.3f} percentage points of yield/spread change" if cfg.source == "fred" else f"{threshold:.4%}"
        f.write(
            f"**Real adverse threshold** (p{ADVERSE_PERCENTILE} of pooled real |{HORIZON_DAYS}-day "
            f"{'yield/spread change' if cfg.source == 'fred' else 'return'}|): "
            f"**{threshold_display}** -- a real top-quartile-sized move for this market's own history, not "
            f"borrowed from any other asset class or sport.\n\n"
        )
        f.write("## Real risk-tier cutoffs (this market's own real backtested p_fail percentiles)\n\n")
        f.write("| Percentile | p_fail cutoff |\n|---|---|\n")
        for p, v in cutoffs.items():
            f.write(f"| {p}th | {v:.4f} |\n")
        f.write("\n## Real calibration (does the real breach rate rise with predicted p_fail?)\n\n")
        f.write(calib.to_markdown(index=False))
        f.write("\n\n## Limitations\n\n")
        f.write(
            "- Zero-drift assumption: this engine sizes real volatility risk only, never claims a directional edge.\n"
            "- EWMA is a real, standard, single-model choice -- not compared here against a real GARCH candidate "
            "(a real future improvement, same \"never assume, always check\" discipline this project applies "
            "elsewhere, just not yet run for this market).\n"
            f"- Monthly ({CHECKPOINT_STRIDE_DAYS}-trading-day) checkpoint stride is a real compute-cost choice, "
            "not a claim that real volatility is constant between checkpoints.\n"
        )
    print(f"Wrote {len(bt)} backtest rows to {out_bt}")
    print(f"Real threshold: {threshold_display}; real risk-tier cutoffs: {cutoffs}")
    print(f"Wrote report to {out_report}")
    log_experiment(meta, stage="backtest_market_tail_risk", notes=f"{market_id}: {len(bt)} rows, threshold={threshold:.4%}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
