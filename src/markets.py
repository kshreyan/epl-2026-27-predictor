"""Central registry for the markets/tail-risk side of this platform --
see config/markets.yaml's own docstring for scope and the real
reasoning behind what's in and out.

Run: python -m src.markets (prints the registry, for a quick sanity check)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETS_CONFIG_PATH = REPO_ROOT / "config" / "markets.yaml"


@dataclass(frozen=True)
class MarketConfig:
    market_id: str
    display_name: str
    country: str
    asset_class: str
    currency: str
    source: str
    tickers: tuple[str, ...]
    # "daily" (default) for every real market with real daily data
    # (Yahoo/Frankfurter/CoinGecko, and most FRED series). "monthly"
    # for a real series FRED only publishes monthly (confirmed for
    # India's own interest-rate series -- OECD-sourced, no real daily
    # India G-Sec/interbank data is free anywhere) -- see
    # backtest_market_tail_risk.py's FREQUENCY_PARAMS for how this
    # changes the real horizon/history/checkpoint cadence rather than
    # forcing monthly data through a daily-shaped window.
    frequency: str = "daily"


def _load_registry() -> dict[str, MarketConfig]:
    with open(MARKETS_CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    registry = {}
    for entry in raw:
        entry = dict(entry)
        entry["tickers"] = tuple(entry["tickers"])
        cfg = MarketConfig(**entry)
        registry[cfg.market_id] = cfg
    return registry


_REGISTRY = _load_registry()


def load_market_config(market_id: str) -> MarketConfig:
    if market_id not in _REGISTRY:
        raise KeyError(
            f"Unknown market_id '{market_id}'. Known markets: {sorted(_REGISTRY)}. "
            f"Add a new entry to {MARKETS_CONFIG_PATH} rather than guessing one."
        )
    return _REGISTRY[market_id]


def all_market_ids() -> list[str]:
    return sorted(_REGISTRY)


def market_path(market_id: str, suffix: str) -> str:
    return f"{market_id}_{suffix}"


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    for mid in all_market_ids():
        cfg = load_market_config(mid)
        print(f"{mid}: {cfg.display_name} ({cfg.country}, {cfg.asset_class}) -- {len(cfg.tickers)} tickers, source={cfg.source}")
