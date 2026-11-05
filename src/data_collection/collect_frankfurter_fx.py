"""Collect real daily FX rates from the Frankfurter API
(api.frankfurter.dev, ECB-sourced) -- confirmed directly this session:
200 OK, real JSON, no key, business-days-only (ECB convention), a real
multi-year date-range query works in one call (5 years / 1,284 real
daily rates confirmed in a single request).

Writes the SAME normalized schema collect_yahoo_prices.py does
(market_id, ticker, date, open, high, low, close, volume, currency,
source_name, source_timestamp, collected_at, is_real_data) so
backtest_market_tail_risk.py/compute_market_tail_risk.py work
unchanged regardless of real source -- open/high/low are all set to
the same single real daily rate (Frankfurter gives one rate per real
business day, no real intraday OHLC), volume is left null (no real
volume concept for a reference FX rate).

A market's own `tickers` in markets.yaml are read here as
"{FROM}{TO}" 6-letter real currency pair codes (e.g. "USDEUR" means
1 real USD expressed in EUR) -- split 3/3 to build the real API query.

Run: python -m src.data_collection.collect_frankfurter_fx --market us_fx
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

SOURCE_NAME = "api.frankfurter.dev (ECB reference rates)"
BASE_URL = "https://api.frankfurter.dev/v1/{start}..{end}"
YEARS_BACK = 5

HISTORICAL_COLUMNS = [
    "market_id", "ticker", "date", "open", "high", "low", "close", "volume",
    "currency", "source_name", "source_timestamp", "collected_at", "is_real_data",
]


def fetch_real_pair_history(from_ccy: str, to_ccy: str, start: str, end: str) -> dict[str, float] | None:
    try:
        resp = requests.get(BASE_URL.format(start=start, end=end), params={"from": from_ccy, "to": to_ccy}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        return {d: rates[to_ccy] for d, rates in payload["rates"].items() if to_ccy in rates}
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"  {from_ccy}{to_ccy}: FAILED real fetch -- {e}")
        return None


def main(market_id: str) -> None:
    cfg = load_market_config(market_id)
    out_path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    collected_at = now_utc_iso()
    end = date.today()
    start = end - timedelta(days=365 * YEARS_BACK)

    rows = []
    n_ok, n_failed = 0, 0
    for ticker in cfg.tickers:
        from_ccy, to_ccy = ticker[:3], ticker[3:]
        series = fetch_real_pair_history(from_ccy, to_ccy, start.isoformat(), end.isoformat())
        if series is None:
            n_failed += 1
            continue
        for d, rate in sorted(series.items()):
            rows.append({
                "market_id": market_id, "ticker": ticker, "date": d,
                "open": rate, "high": rate, "low": rate, "close": rate, "volume": "",
                "currency": to_ccy, "source_name": SOURCE_NAME, "source_timestamp": d,
                "collected_at": collected_at, "is_real_data": True,
            })
        n_ok += 1
        print(f"  {ticker}: {len(series)} real daily rates")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real daily rates for {n_ok}/{len(cfg.tickers)} pairs to {out_path} ({n_failed} failed)")
    log_data_version(
        dataset_name=f"{market_id}_historical_prices", source_name=SOURCE_NAME,
        source_timestamp=collected_at, row_count=len(rows), is_real_data=True,
        notes=f"{n_ok}/{len(cfg.tickers)} pairs real-fetched, {n_failed} failed",
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
