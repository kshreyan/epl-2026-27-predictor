"""Builds the markets-side dashboard JSON (data/outputs/dashboard/
{market_id}_tail_risk.json) -- the markets equivalent of
build_margin_survival_json.py, one real tail-risk row per instrument,
no eligibility filter, same "every row, every tier, nothing hidden"
discipline the soccer/NFL/NBA engines already use.

Run: python -m src.dashboard.build_market_dashboard_json
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.dashboard.build_dashboard_json import _to_records, _write_json  # noqa: E402
from src.markets import all_market_ids, load_market_config, market_path  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "outputs"


def build_market_json(market_id: str) -> None:
    cfg = load_market_config(market_id)
    path = OUT_DIR / market_path(market_id, "tail_risk.csv")
    if not path.exists():
        _write_json(f"{market_id}_tail_risk.json", {
            "market_id": market_id, "display_name": cfg.display_name, "country": cfg.country,
            "asset_class": cfg.asset_class, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
            "record_count": 0, "data": [], "status": "not_yet_available",
            "note": "No tail-risk predictions yet -- run compute_market_tail_risk.py first.",
        })
        return

    df = pd.read_csv(path)
    tally = df["risk_label"].value_counts().to_dict()
    payload = {
        "market_id": market_id, "display_name": cfg.display_name, "country": cfg.country,
        "asset_class": cfg.asset_class, "currency": cfg.currency,
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "record_count": len(df), "risk_tier_tally": tally,
        "engine_note": (
            f"Real EWMA-volatility tail-risk read for every real instrument in {cfg.display_name}'s universe -- "
            f"P(return over the next real trading week falls below this market's own real backtested adverse "
            f"threshold), bucketed into the same 5-tier risk shape every other engine on this site uses. "
            f"Zero real drift assumed -- this is a volatility/tail-risk read only, never a directional "
            f"(up/down) call. Not investment advice."
        ),
        "data": _to_records(df),
    }
    _write_json(f"{market_id}_tail_risk.json", payload)


def build_markets_manifest() -> None:
    """A small manifest of every active market (id + display name +
    country + asset class) -- the markets equivalent of
    build_dashboard_json.py's leagues.json -- so the site's markets
    switcher never has to hardcode the list; adding a new entry to
    config/markets.yaml is enough for it to appear."""
    markets = [
        {
            "market_id": mid, "display_name": load_market_config(mid).display_name,
            "country": load_market_config(mid).country, "asset_class": load_market_config(mid).asset_class,
        }
        for mid in all_market_ids()
    ]
    _write_json("markets.json", {"generated_at": now_utc_iso(), "markets": markets})


def main() -> None:
    for market_id in all_market_ids():
        build_market_json(market_id)
    build_markets_manifest()


if __name__ == "__main__":
    main()
