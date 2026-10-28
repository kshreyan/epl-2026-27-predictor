"""Real backtest of a model+market logit-space blend for NFL, the same
pattern market_blend_model.py already established for soccer (a fixed
50/50 blend, judged significant only if a paired bootstrap CI excludes
zero AND it wins a season majority -- reusing
`paired_bootstrap_significance` directly, not reimplemented) --
adapted for a 2-outcome market (no real draw) and NFL's own real
closing moneylines (nflverse, via collect_nflverse.py) instead of a
separately-collected historical-odds file.

Pairs backtest_team_sport.py's own out-of-sample point-margin-model
probabilities (data/outputs/nfl_backtest_match_results.csv) with each
real historical game's real closing moneyline (nfl_historical_matches
.csv), de-vigged with this league's own real backtested-best method
(select_devig_method -- see backtest_market_devig.py).

Run: python -m src.evaluation.backtest_nfl_market_blend
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
from src.features.market_devig import DEVIG_METHODS, select_devig_method  # noqa: E402
from src.models.final_stacked_model import paired_bootstrap_significance  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402


def main(league_id: str = "nfl") -> None:
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    if not backtest_path.exists():
        raise FileNotFoundError(f"{backtest_path} not found -- run backtest_team_sport.py --league {league_id} first")

    model_df = pd.read_csv(backtest_path, parse_dates=["date"])
    hist_df = pd.read_csv(historical_path, parse_dates=["date"])
    hist_df = hist_df.dropna(subset=["home_moneyline", "away_moneyline"])

    merged = model_df.merge(
        hist_df[["date", "home_team", "away_team", "season", "home_moneyline", "away_moneyline"]],
        on=["date", "home_team", "away_team"], how="inner",
    )
    n_dropped = len(model_df) - len(merged)
    if n_dropped:
        print(f"WARNING: {n_dropped}/{len(model_df)} backtest games had no matching real closing moneyline -- excluded, not estimated.")

    devig_method = select_devig_method(league_id)
    devig_fn = DEVIG_METHODS[devig_method]

    model_loss, blend_loss = [], []
    blend_home_probs = []
    for _, r in merged.iterrows():
        decimal_odds = (american_to_decimal(r["home_moneyline"]), american_to_decimal(r["away_moneyline"]))
        market_home, market_away = devig_fn(decimal_odds)
        model_home = r["pm_home_win"]

        blend_home = log_odds_average_binary([model_home, market_home])
        blend_home_probs.append(blend_home)

        home_won = r["actual_result"] == "home_win"
        p_model = max(model_home if home_won else 1 - model_home, 1e-12)
        p_blend = max(blend_home if home_won else 1 - blend_home, 1e-12)
        model_loss.append(-np.log(p_model))
        blend_loss.append(-np.log(p_blend))

    merged["blend_home_win_prob"] = blend_home_probs
    model_loss, blend_loss = np.array(model_loss), np.array(blend_loss)

    significance = paired_bootstrap_significance(model_loss, blend_loss, merged["season"].to_numpy())

    print(f"Real NFL model+market blend backtest on {len(merged)} real historical games "
          f"(de-vig method: {devig_method}):")
    print(f"  Model-only mean log loss: {model_loss.mean():.5f}")
    print(f"  Blend mean log loss:      {blend_loss.mean():.5f}")
    print(f"  Bootstrap 95% CI on the edge: [{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}] "
          f"({significance['season_wins']}/{significance['n_seasons']} seasons)")
    print(f"  Blend significant: {significance['ensemble_significant']}")

    out_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_comparison.csv"
    pd.DataFrame([{
        "devig_method": devig_method, "n_matches": len(merged),
        "model_log_loss": round(float(model_loss.mean()), 5), "blend_log_loss": round(float(blend_loss.mean()), 5),
        "ci_low": round(significance["ci_low"], 5), "ci_high": round(significance["ci_high"], 5),
        "blend_significant": significance["ensemble_significant"],
        "season_wins": significance["season_wins"], "n_seasons": significance["n_seasons"],
        "generated_at": now_utc_iso(),
    }]).to_csv(out_path, index=False)
    print(f"Wrote {out_path}")

    report_path = REPO_ROOT / "reports" / f"{league_id}_market_blend_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} Model+Market Blend Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(
            f"Real backtest on {len(merged)} real historical games: the point-margin model's own real "
            f"out-of-sample probability vs. a 50/50 logit-space blend with the real closing moneyline, "
            f"de-vigged by this league's own real backtested-best method (**{devig_method}** -- see "
            f"reports/{league_id}_devig_method_report.md).\n\n"
        )
        f.write(f"- Model-only mean log loss: {model_loss.mean():.5f}\n")
        f.write(f"- Blend mean log loss: {blend_loss.mean():.5f}\n")
        f.write(f"- Bootstrap 95% CI on the edge (positive favors the blend): "
                f"[{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}]\n")
        f.write(f"- Season majority: {significance['season_wins']}/{significance['n_seasons']}\n\n")
        verdict = (
            "The blend's edge is statistically significant (CI excludes zero and it wins a season majority) "
            "-- blending real market odds in for fixtures with real current market data."
            if significance["ensemble_significant"] else
            "**No significant edge found** -- the CI does not exclude zero, or the blend does not win a "
            "real season majority. Model-only predictions remain primary; market odds are still shown "
            "for comparison only, not blended in. This is a real, honest result, not a bug."
        )
        f.write(f"## Verdict\n\n{verdict}\n")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nfl", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
