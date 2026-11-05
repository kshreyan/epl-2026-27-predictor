"""Collect real daily Treasury yield / credit-spread series from FRED
(fred.stlouisfed.org/graph/fredgraph.csv) -- confirmed directly this
session: 200 OK, real CSV, no key, real history back to 1962 for the
Treasury series, current through today.

Writes the SAME normalized schema collect_yahoo_prices.py does, with
one real adaptation: a FRED series has no real "price" concept at
all -- it's a yield (e.g. DGS10, percent) or a credit spread (e.g.
BAMLH0A0HYM2, basis points expressed as percent) LEVEL. That level is
written into the `close` column (open/high/low mirror it, volume
null) so backtest_market_tail_risk.py's generic log-return machinery
still applies -- except here a "return" is a real day-over-day CHANGE
IN YIELD/SPREAD LEVEL (duration/credit risk), not a price return. This
is the real, standard way fixed-income risk is actually measured
(yield-change volatility), not a forced reuse of an equity-shaped
concept.

FRED marks a real missing observation (holiday, data not yet
published) with "." for most series, but confirmed directly this
session: at least one real series (DGS3MO) uses a genuinely empty
string instead for some historical rows -- both are treated as a real
missing observation here, skipped, never estimated.

Run: python -m src.data_collection.collect_fred_series --market us_fixed_income_credit
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

SOURCE_NAME = "fred.stlouisfed.org/graph/fredgraph.csv"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

HISTORICAL_COLUMNS = [
    "market_id", "ticker", "date", "open", "high", "low", "close", "volume",
    "currency", "source_name", "source_timestamp", "collected_at", "is_real_data",
]


def fetch_real_series(series_id: str) -> list[tuple[str, float]] | None:
    try:
        resp = requests.get(FRED_URL, params={"id": series_id}, timeout=20)
        resp.raise_for_status()
        rows = list(csv.reader(io.StringIO(resp.text)))
        out = []
        for d, v in rows[1:]:
            if v in (".", ""):  # real missing observation -- skipped, not estimated
                continue
            out.append((d, float(v)))
        return out
    except (requests.RequestException, ValueError, IndexError) as e:
        print(f"  {series_id}: FAILED real fetch -- {e}")
        return None


def main(market_id: str) -> None:
    cfg = load_market_config(market_id)
    out_path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    collected_at = now_utc_iso()

    rows = []
    n_ok, n_failed = 0, 0
    for series_id in cfg.tickers:
        series = fetch_real_series(series_id)
        if series is None:
            n_failed += 1
            continue
        for d, v in series:
            rows.append({
                "market_id": market_id, "ticker": series_id, "date": d,
                "open": v, "high": v, "low": v, "close": v, "volume": "",
                "currency": cfg.currency, "source_name": SOURCE_NAME, "source_timestamp": d,
                "collected_at": collected_at, "is_real_data": True,
            })
        n_ok += 1
        print(f"  {series_id}: {len(series)} real daily observations")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real daily observations for {n_ok}/{len(cfg.tickers)} series to {out_path} ({n_failed} failed)")
    log_data_version(
        dataset_name=f"{market_id}_historical_prices", source_name=SOURCE_NAME,
        source_timestamp=collected_at, row_count=len(rows), is_real_data=True,
        notes=f"{n_ok}/{len(cfg.tickers)} series real-fetched, {n_failed} failed",
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
