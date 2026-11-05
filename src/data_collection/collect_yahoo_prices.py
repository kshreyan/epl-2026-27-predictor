"""Collect real daily OHLCV price history for a market's instrument
universe from Yahoo Finance's unofficial chart API
(query1.finance.yahoo.com/v8/finance/chart/{ticker}) -- confirmed
directly this session: 200 OK, real JSON, a `User-Agent` header is
required (a bare request without one is rejected), no API key.

This is the shared real source for every markets.yaml asset class
built on individual tradeable instruments (equities, commodity
futures via their own real futures tickers e.g. "GC=F", REIT/liquid-
alt ETF proxies for real assets/alternatives, and Indian equities/
REITs via the same endpoint with a ".NS" ticker suffix) -- fixed
income/credit (FRED), FX (Frankfurter), and digital assets (CoinGecko)
each get their own collector since they're genuinely different real
sources, not this one.

Real, honest limitation: this is a single unauthenticated public
endpoint Yahoo does not formally document as an API -- it can change
or rate-limit without notice. No fallback/retry beyond what's below;
a failed ticker is reported and skipped, never silently dropped or
estimated.

Run: python -m src.data_collection.collect_yahoo_prices --market us_equities
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

SOURCE_NAME = "query1.finance.yahoo.com (unofficial chart API)"
HEADERS = {"User-Agent": "Mozilla/5.0"}
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
RANGE = "5y"
REQUEST_DELAY_SECONDS = 0.3  # real, polite pacing -- no documented rate limit, but none confirmed absent either

HISTORICAL_COLUMNS = [
    "market_id", "ticker", "date", "open", "high", "low", "close", "volume",
    "currency", "source_name", "source_timestamp", "collected_at", "is_real_data",
]


def fetch_real_ticker_history(ticker: str) -> dict | None:
    """One real ticker's full chart payload, or None if this real
    fetch failed (reported by the caller, never retried silently into
    a guessed value)."""
    try:
        resp = requests.get(
            CHART_URL.format(ticker=ticker), params={"range": RANGE, "interval": "1d"},
            headers=HEADERS, timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        result = payload["chart"]["result"]
        if not result:
            return None
        return result[0]
    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        print(f"  {ticker}: FAILED real fetch -- {e}")
        return None


def main(market_id: str) -> None:
    cfg = load_market_config(market_id)
    out_path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    collected_at = now_utc_iso()

    rows = []
    n_ok, n_failed = 0, 0
    for ticker in cfg.tickers:
        result = fetch_real_ticker_history(ticker)
        time.sleep(REQUEST_DELAY_SECONDS)
        if result is None:
            n_failed += 1
            continue
        timestamps = result.get("timestamp") or []
        quote = result["indicators"]["quote"][0]
        meta = result["meta"]
        source_timestamp = str(meta.get("regularMarketTime", ""))
        n_rows_for_ticker = 0
        for i, ts in enumerate(timestamps):
            o, h, lo, c, v = quote["open"][i], quote["high"][i], quote["low"][i], quote["close"][i], quote["volume"][i]
            if o is None or c is None:  # real gaps (e.g. a real holiday inside the range) -- skipped, not estimated
                continue
            date = time.strftime("%Y-%m-%d", time.gmtime(ts))
            rows.append({
                "market_id": market_id, "ticker": ticker, "date": date,
                "open": o, "high": h, "low": lo, "close": c, "volume": v,
                "currency": meta.get("currency", cfg.currency),
                "source_name": SOURCE_NAME, "source_timestamp": source_timestamp,
                "collected_at": collected_at, "is_real_data": True,
            })
            n_rows_for_ticker += 1
        n_ok += 1
        print(f"  {ticker}: {n_rows_for_ticker} real daily bars")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real daily bars for {n_ok}/{len(cfg.tickers)} tickers to {out_path} ({n_failed} failed)")
    log_data_version(
        dataset_name=f"{market_id}_historical_prices", source_name=SOURCE_NAME,
        source_timestamp=collected_at, row_count=len(rows), is_real_data=True,
        notes=f"{n_ok}/{len(cfg.tickers)} tickers real-fetched, {n_failed} failed",
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
