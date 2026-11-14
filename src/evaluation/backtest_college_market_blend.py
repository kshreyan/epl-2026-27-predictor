"""Real backtest of a model+market logit-space blend for NCAA Football
or NCAA Basketball -- same pattern as backtest_nfl_market_blend.py /
backtest_nba_market.py (a fixed 50/50 blend in logit space, judged
significant only via paired_bootstrap_significance's CI-excludes-zero
AND season-majority test), but for a real closing moneyline collected
into its own separate file keyed by match_id
(collect_espn_ncaaf_odds.py / collect_espn_college_basketball_odds.py,
both ESPN real game-summary pickcenter, same real DraftKings-sourced
source NFL/NBA already use) rather than one embedded directly in
historical_matches.csv (NFL's real nflverse schema) or NBA's own
separate-but-differently-shaped file.

Pairs predict_team_sport_matches.py's own real primary moneyline model
for each league (`elo_` for both NCAAF and NCAAB -- confirmed via
should_use_point_margin_model(), never assumed) with the real closing
line, de-vigged with this league's own real backtested-best method
(select_devig_method).

Run: python -m src.evaluation.backtest_college_market_blend --league ncaaf
(also accepts ncaab)
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
from src.models.predict_team_sport_matches import should_use_point_margin_model  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

# home/away column prefix for each league's real primary moneyline
# model, per should_use_point_margin_model() -- confirmed False for
# both NCAAF and NCAAB this session, i.e. "elo_" for both; computed
# fresh below rather than hardcoded, in case a future recalibration
# flips either one.


def main(league_id: str) -> None:
    odds_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    hist_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    if not backtest_path.exists():
        raise FileNotFoundError(f"{backtest_path} not found -- run backtest_team_sport.py --league {league_id} first")

    prefix = "pm_" if should_use_point_margin_model(league_id) else "elo_"
    home_col, away_col = f"{prefix}home_win", f"{prefix}away_win"

    odds_df = pd.read_csv(odds_path)
    hist_df = pd.read_csv(hist_path)[["match_id", "season", "date", "home_team", "away_team"]]
    model_df = pd.read_csv(backtest_path, parse_dates=["date"])

    odds_with_game = odds_df.merge(hist_df, on="match_id", how="inner")
    odds_with_game["date"] = pd.to_datetime(odds_with_game["date"])
    model_dedup = model_df.drop_duplicates(subset=["date", "home_team", "away_team"], keep=False)
    merged = odds_with_game.merge(model_dedup, on=["date", "home_team", "away_team"], how="inner")
    n_dropped = len(odds_with_game) - len(merged)
    if n_dropped:
        print(f"WARNING: {n_dropped}/{len(odds_with_game)} real odds rows had no matching real backtest row -- excluded, not estimated.")

    devig_method = select_devig_method(league_id)
    devig_fn = DEVIG_METHODS[devig_method]

    # NCAAF's real collector (collect_espn_ncaaf_odds.py) only has one
    # real consensus moneyline per game (no real open/close
    # distinction -- confirmed directly, see that script's own
    # docstring); NCAAB's does have both (collect_espn_college_
    # basketball_odds.py), so this uses whichever real column the
    # league's own collector actually produced, never assuming one
    # schema fits both.
    home_ml_col = "home_moneyline_close" if "home_moneyline_close" in merged.columns else "home_moneyline"
    away_ml_col = "away_moneyline_close" if "away_moneyline_close" in merged.columns else "away_moneyline"

    model_loss, blend_loss = [], []
    blend_home_probs = []
    for _, r in merged.iterrows():
        decimal_odds = (american_to_decimal(r[home_ml_col]), american_to_decimal(r[away_ml_col]))
        market_home, _market_away = devig_fn(decimal_odds)
        model_home = r[home_col]

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

    print(f"Real {league_id.upper()} model+market blend backtest on {len(merged)} real historical games "
          f"(primary model column: {home_col}, de-vig method: {devig_method}):")
    print(f"  Model-only mean log loss: {model_loss.mean():.5f}")
    print(f"  Blend mean log loss:      {blend_loss.mean():.5f}")
    print(f"  Bootstrap 95% CI on the edge: [{significance['ci_low']:+.5f}, {significance['ci_high']:+.5f}] "
          f"({significance['season_wins']}/{significance['n_seasons']} seasons)")
    print(f"  Blend significant: {significance['ensemble_significant']}")

    out_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_comparison.csv"
    pd.DataFrame([{
        "devig_method": devig_method, "primary_model_column": home_col, "n_matches": len(merged),
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
            f"Real backtest on {len(merged)} real historical games (one real recent season -- see "
            f"collect_espn_{'ncaaf' if league_id == 'ncaaf' else 'college_basketball'}_odds.py for the "
            f"real closing-line collection's own deliberate scope limit): this league's own real primary "
            f"moneyline model ({home_col}) vs. a 50/50 logit-space blend with the real closing moneyline, "
            f"de-vigged by this league's own real backtested-best method (**{devig_method}**).\n\n"
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
    _parser.add_argument("--league", required=True, choices=["ncaaf", "ncaab"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
