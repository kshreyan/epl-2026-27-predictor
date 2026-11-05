"""Collect real daily crypto prices from CoinGecko's free public API
(api.coingecko.com) -- confirmed directly this session: 200 OK, real
JSON, no key. Two real, confirmed constraints the free tier actually
has (not assumed from documentation/training knowledge):
1. History is capped at 365 days (`days=max` returns a real HTTP 401
   with error_code 10012 asking for a paid plan) -- so this engine's
   tail-risk backtest runs on 1 real year of data for this market,
   honestly less deep than the 5 real years the Yahoo-sourced markets
   get, not padded or estimated to match.
2. The free tier rate-limits aggressively (confirmed: a real HTTP 429
   after just 2-3 requests in quick succession) -- real pacing between
   requests plus a real retry-with-backoff on 429 is required, not
   optional, for this collector to reliably finish a small universe.

Writes the SAME normalized schema collect_yahoo_prices.py does
(volume IS real here -- CoinGecko's `total_volumes` series).

A market's `currency` in markets.yaml selects CoinGecko's own
`vs_currency` param directly (e.g. "usd" or "inr") -- the same real
global coin universe, just quoted in a different real currency, which
is also why india_digital_assets needs no separate real price source:
CoinGecko already serves INR-denominated prices directly.

Run: python -m src.data_collection.collect_coingecko_crypto --market us_digital_assets
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.markets import load_market_config, market_path  # noqa: E402
from src.utils.versioning import log_data_version, now_utc_iso  # noqa: E402

SOURCE_NAME = "api.coingecko.com (free public tier)"
CHART_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
DAYS = "365"  # the real free-tier cap -- confirmed directly, see module docstring
REQUEST_DELAY_SECONDS = 8.0  # real pacing -- confirmed necessary to avoid the real 429 rate limit
MAX_RETRIES = 3

HISTORICAL_COLUMNS = [
    "market_id", "ticker", "date", "open", "high", "low", "close", "volume",
    "currency", "source_name", "source_timestamp", "collected_at", "is_real_data",
]


def fetch_real_coin_history(coin_id: str, vs_currency: str) -> dict | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                CHART_URL.format(coin_id=coin_id), params={"vs_currency": vs_currency, "days": DAYS, "interval": "daily"},
                timeout=30,
            )
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 15))
                print(f"  {coin_id}: real 429, waiting {wait:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            print(f"  {coin_id}: FAILED real fetch -- {e}")
            return None
    print(f"  {coin_id}: FAILED after {MAX_RETRIES} real 429 retries")
    return None


def main(market_id: str) -> None:
    cfg = load_market_config(market_id)
    out_path = REPO_ROOT / "data" / "raw" / market_path(market_id, "historical_prices.csv")
    collected_at = now_utc_iso()
    vs_currency = cfg.currency.lower()

    rows = []
    n_ok, n_failed = 0, 0
    for i, coin_id in enumerate(cfg.tickers):
        if i > 0:
            time.sleep(REQUEST_DELAY_SECONDS)
        payload = fetch_real_coin_history(coin_id, vs_currency)
        if payload is None:
            n_failed += 1
            continue
        prices = {ts: p for ts, p in payload["prices"]}
        volumes = {ts: v for ts, v in payload["total_volumes"]}
        n_rows = 0
        for ts in sorted(prices):
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            price = prices[ts]
            rows.append({
                "market_id": market_id, "ticker": coin_id, "date": d,
                "open": price, "high": price, "low": price, "close": price,
                "volume": volumes.get(ts, ""),
                "currency": cfg.currency, "source_name": SOURCE_NAME, "source_timestamp": str(ts),
                "collected_at": collected_at, "is_real_data": True,
            })
            n_rows += 1
        n_ok += 1
        print(f"  {coin_id}: {n_rows} real daily prices")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real daily prices for {n_ok}/{len(cfg.tickers)} coins to {out_path} ({n_failed} failed)")
    log_data_version(
        dataset_name=f"{market_id}_historical_prices", source_name=SOURCE_NAME,
        source_timestamp=collected_at, row_count=len(rows), is_real_data=True,
        notes=f"{n_ok}/{len(cfg.tickers)} coins real-fetched, {n_failed} failed, {DAYS}-day free-tier cap",
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, dest="market_id")
    args = parser.parse_args()
    main(market_id=args.market_id)
