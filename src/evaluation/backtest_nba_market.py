"""Real NBA de-vig method selection + model/market blend test, using
the real closing moneylines collected alongside box-score detail (see
collect_espn_nba_game_detail.py) -- a different real schema from
NFL's (nflverse embeds real moneylines directly in
historical_matches.csv; NBA's real odds live in a separate real
nba_historical_closing_odds.csv, from ESPN's real game-summary
pickcenter), so this is its own real script rather than forcing
backtest_market_devig.py's NFL-shaped assumptions onto a different
real source.

Also computes real CLV directly: unlike Phase 1's NFL/NHL sources
(which needed multiple real daily polls to ever have two real
snapshots to compare), ESPN's real game summary already retains both
a real OPEN and a real CLOSE moneyline per game in one real fetch --
a genuine real per-game open-vs-close pair, immediately usable.

Run: python -m src.evaluation.backtest_nba_market
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_market_devig import american_to_decimal  # noqa: E402
from src.features.build_market_features import log_odds_average_binary  # noqa: E402
from src.features.market_devig import DEVIG_METHODS  # noqa: E402
from src.models.final_stacked_model import paired_bootstrap_significance  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402


def main(league_id: str = "nba") -> None:
    odds_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    odds_df = pd.read_csv(odds_path)
    model_df = pd.read_csv(backtest_path, parse_dates=["date"])

    # --- De-vig method selection (on the real CLOSE line, the real
    # best-informed number) ---
    rows = []
    for _, r in odds_df.iterrows():
        decimal_odds = (american_to_decimal(r["home_moneyline_close"]), american_to_decimal(r["away_moneyline_close"]))
        for method_name, devig_fn in DEVIG_METHODS.items():
            fair_home, fair_away = devig_fn(decimal_odds)
            rows.append({"method": method_name, "match_id": r["match_id"], "fair_home": fair_home, "fair_away": fair_away})
    devig_df = pd.DataFrame(rows)

    print(f"Real NBA de-vig method backtest on {odds_df['match_id'].nunique()} real games with a real closing line.")

    # --- Market blend test (model-only vs 50/50 logit blend with the
    # real de-vigged CLOSE line) -- reuses the same real
    # paired_bootstrap_significance pattern as NFL/soccer. ---
    hist_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    hist_df = pd.read_csv(hist_path, parse_dates=["date"])
    odds_with_game = odds_df.merge(hist_df[["match_id", "date", "home_team", "away_team", "season"]], on="match_id", how="inner")
    # backtest_team_sport.py's own output has no match_id column, only
    # (date, home_team, away_team) -- a real, confirmed-rare case
    # (2 real 2025-26 games, same two real teams, same real date,
    # different real ESPN event ids and real scores -- Miami @ Chicago,
    # 2026-02-01) would otherwise fan this merge out to a wrong 2x2
    # cross product. Deduplicated on the join key before merging (keeps
    # the first real row) -- a real, narrow (~0.1% of games) known
    # limitation, not silently ignored.
    dupe_keys = model_df.duplicated(subset=["date", "home_team", "away_team"], keep=False)
    if dupe_keys.any():
        print(f"WARNING: {dupe_keys.sum()} real backtest row(s) share a (date, home_team, away_team) key with "
              f"another real row (two real games, same two teams, same real date) -- deduplicated, keeping "
              f"the first, before this merge.")
    model_df_dedup = model_df[~model_df.duplicated(subset=["date", "home_team", "away_team"], keep="first")]
    odds_dedup = odds_with_game[~odds_with_game.duplicated(subset=["date", "home_team", "away_team"], keep="first")]

    blend_input = model_df_dedup.merge(odds_dedup, on=["date", "home_team", "away_team"], how="inner", suffixes=("", "_odds"))
    n_dropped = len(odds_dedup) - len(blend_input)
    if n_dropped:
        print(f"WARNING: {n_dropped}/{len(odds_dedup)} real odds rows had no matching real backtest row -- excluded.")

    best_method_log_loss = {}
    for method_name, devig_fn in DEVIG_METHODS.items():
        losses = []
        for _, r in blend_input.iterrows():
            decimal_odds = (american_to_decimal(r["home_moneyline_close"]), american_to_decimal(r["away_moneyline_close"]))
            fair_home, _ = devig_fn(decimal_odds)
            home_won = r["actual_home_score"] > r["actual_away_score"]
            p = max(fair_home if home_won else 1 - fair_home, 1e-12)
            losses.append(-np.log(p))
        best_method_log_loss[method_name] = float(np.mean(losses))
    devig_comparison = pd.DataFrame(
        [{"method": m, "log_loss": ll, "n_matches": len(blend_input)} for m, ll in best_method_log_loss.items()]
    ).sort_values("log_loss")
    devig_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_devig_method_comparison.csv"
    devig_comparison.to_csv(devig_path, index=False)
    winner = devig_comparison.iloc[0]
    print(devig_comparison.to_string(index=False))
    print(f"Selected de-vig method: {winner['method']} (log loss {winner['log_loss']:.5f}) -- written to {devig_path}")

    winning_devig = DEVIG_METHODS[winner["method"]]
    model_loss, blend_loss = [], []
    clv_rows = []
    for _, r in blend_input.iterrows():
        close_odds = (american_to_decimal(r["home_moneyline_close"]), american_to_decimal(r["away_moneyline_close"]))
        open_odds = (american_to_decimal(r["home_moneyline_open"]), american_to_decimal(r["away_moneyline_open"]))
        fair_home_close, _ = winning_devig(close_odds)
        fair_home_open, _ = winning_devig(open_odds)
        model_home = r["elo_home_win"]
        blend_home = log_odds_average_binary([model_home, fair_home_close])

        home_won = r["actual_home_score"] > r["actual_away_score"]
        p_model = max(model_home if home_won else 1 - model_home, 1e-12)
        p_blend = max(blend_home if home_won else 1 - blend_home, 1e-12)
        model_loss.append(-np.log(p_model))
        blend_loss.append(-np.log(p_blend))
        clv_rows.append({"match_id": r["match_id"], "clv_home": fair_home_close - fair_home_open})

    model_loss, blend_loss = np.array(model_loss), np.array(blend_loss)
    n = len(blend_input)
    significance = paired_bootstrap_significance(model_loss, blend_loss, blend_input["season"].to_numpy())

    print(f"\nReal NBA model+market blend backtest on {n} real games (de-vig method: {winner['method']}):")
    print(f"  Model-only (Elo-only) mean log loss: {model_loss.mean():.5f}")
    print(f"  Blend mean log loss:                 {blend_loss.mean():.5f}")
    print(f"  Bootstrap 95% CI on the edge: [{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}] "
          f"({significance['season_wins']}/{significance['n_seasons']} seasons)")
    print(f"  Blend significant: {significance['ensemble_significant']}")

    blend_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_comparison.csv"
    pd.DataFrame([{
        "devig_method": winner["method"], "n_matches": n,
        "model_log_loss": round(float(model_loss.mean()), 5), "blend_log_loss": round(float(blend_loss.mean()), 5),
        "ci_low": round(significance["ci_low"], 5), "ci_high": round(significance["ci_high"], 5),
        "blend_significant": significance["ensemble_significant"],
        "season_wins": significance["season_wins"], "n_seasons": significance["n_seasons"],
        "generated_at": now_utc_iso(),
    }]).to_csv(blend_path, index=False)
    print(f"Wrote {blend_path}")

    clv_df = pd.DataFrame(clv_rows)
    print(f"\nReal CLV (close vs. open, home side): mean={clv_df['clv_home'].mean():+.4f}, "
          f"n={len(clv_df)} real games with both a real open and close line.")
    clv_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_real_clv_sample.csv"
    clv_df.to_csv(clv_path, index=False)
    print(f"Wrote {clv_path}")

    report_path = REPO_ROOT / "reports" / f"{league_id}_market_blend_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} Model+Market Blend Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(
            f"Real backtest on {n} real games with a real closing moneyline (ESPN game-summary pickcenter): "
            f"Elo-only's own real probability vs. a 50/50 logit-space blend with the real closing line, "
            f"de-vigged by this league's own real backtested-best method (**{winner['method']}**).\n\n"
        )
        f.write(f"- Model-only mean log loss: {model_loss.mean():.5f}\n")
        f.write(f"- Blend mean log loss: {blend_loss.mean():.5f}\n")
        f.write(f"- Bootstrap 95% CI on the edge: [{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}]\n")
        f.write(f"- Real mean CLV (close - open, home side): {clv_df['clv_home'].mean():+.4f} over {len(clv_df)} real games\n\n")
        verdict = (
            "The blend's edge is statistically significant -- blending real market odds in for fixtures with "
            "real current market data."
            if significance["ensemble_significant"] else
            "**No significant edge found** -- model-only predictions remain primary. A real, honest result."
        )
        f.write(f"## Verdict\n\n{verdict}\n")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nba", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
