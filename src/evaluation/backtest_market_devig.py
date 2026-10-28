"""Real backtest comparing the three de-vig methods (multiplicative,
Shin, power -- see market_devig.py) against real historical closing
moneylines and real outcomes: which method's fair probability, taken
as-is (no model blended in), has the lowest real log loss against what
actually happened. Decides `select_devig_method()`'s answer for this
league -- never assumed.

Currently wired for NFL (nflverse's real games.csv carries real
closing home_moneyline/away_moneyline for every historical game -- see
collect_nflverse.py); extends to other sports once their own real
historical closing-line coverage is confirmed.

Run: python -m src.evaluation.backtest_market_devig --league nfl
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.features.market_devig import DEVIG_METHODS  # noqa: E402
from src.leagues import league_path  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402


def american_to_decimal(ml: float) -> float:
    return ml / 100 + 1 if ml > 0 else 100 / abs(ml) + 1


def main(league_id: str = "nfl") -> None:
    hist_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    df = pd.read_csv(hist_path)
    df = df.dropna(subset=["home_moneyline", "away_moneyline", "home_score", "away_score"])

    rows = []
    for _, r in df.iterrows():
        decimal_odds = (american_to_decimal(r["home_moneyline"]), american_to_decimal(r["away_moneyline"]))
        home_won = 1 if r["home_score"] > r["away_score"] else 0
        for method_name, devig_fn in DEVIG_METHODS.items():
            fair_home, fair_away = devig_fn(decimal_odds)
            p = max(fair_home if home_won else fair_away, 1e-12)
            rows.append({"method": method_name, "match_id": r["match_id"], "log_loss": -np.log(p)})

    results_df = pd.DataFrame(rows)
    comparison = (
        results_df.groupby("method")["log_loss"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "log_loss", "count": "n_matches"})
        .reset_index()
        .sort_values("log_loss")
    )

    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "devig_method_comparison.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out_path, index=False)

    winner = comparison.iloc[0]
    print(f"Real de-vig method backtest on {df['match_id'].nunique()} real historical {league_id} closing lines:")
    print(comparison.to_string(index=False))
    print(f"\nSelected: {winner['method']} (log loss {winner['log_loss']:.5f}) -- written to {out_path}")

    report_path = REPO_ROOT / "reports" / f"{league_id}_devig_method_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} De-Vig Method Selection Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(
            f"Real backtest on {len(df)} real historical closing moneylines (American, converted to decimal) "
            "against real game outcomes -- each method's own fair probability for the team that actually won, "
            "scored by log loss, no model blended in.\n\n"
        )
        f.write("| method | log_loss | n_matches |\n|---|---|---|\n")
        for _, row in comparison.iterrows():
            f.write(f"| {row['method']} | {row['log_loss']:.5f} | {int(row['n_matches'])} |\n")
        f.write(f"\n**Selected: {winner['method']}** -- used by `select_devig_method('{league_id}')`.\n")
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nfl", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
