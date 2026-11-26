"""Real model+market blend backtest for a UEFA club competition (UCL
or UEL), closing the one real gap market_blend_model.py's own
docstring used to document: "no historical-odds source exists for
this competition (no football-data.co.uk coverage)". That line was
narrower than it read -- true of football-data.co.uk specifically,
but ESPN's real soccer game-summary endpoint (same real DraftKings
pickcenter source this project already uses for NBA) carries real
3-way (home/draw/away) odds for UCL/UEL too, confirmed directly this
session, with a real open/close distinction. See
collect_espn_continental_cup_odds.py for the collector (one real
recent season, 2025-26 -- same deliberate scope limit as every other
ESPN-sourced odds collector in this project).

Pairs this competition's own real backtest (backtest_continental_cup
.py's output, data/outputs/{league}_backtest_match_results.csv --
whichever model that backtest found wins for this competition,
Dixon-Coles or Elo) with the real close line, de-vigged (simple
proportional normalization, same as market_blend_model.py's domestic
3-way de-vig -- only one real bookmaker per match here, so there is
no cross-bookmaker average to take) and blended 50/50 in logit space
(src.features.build_market_features.log_odds_average, the exact same
function market_blend_model.py already uses, not reimplemented).
Judged significant only via the same paired-bootstrap-CI-excludes-zero
test every other blend in this project is held to
(paired_bootstrap_significance) -- `n_bootstrap` per-season breakdown
will only ever show one real season here (2025-26 is the only season
with real ESPN odds collected), same honest "1/1 seasons" caveat NBA's
own market blend already carries.

Run: python -m src.evaluation.backtest_continental_cup_market_blend --league ucl
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import brier_row, log_loss_row, rps  # noqa: E402
from src.evaluation.backtest_market_devig import american_to_decimal  # noqa: E402
from src.features.build_market_features import log_odds_average, remove_overround  # noqa: E402
from src.models.final_stacked_model import paired_bootstrap_significance  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

# Whichever model backtest_continental_cup.py's own real backtest found
# wins for this competition -- confirmed per league by reading each
# one's own reports/{league}_model_selection_report.md, never assumed
# to generalize from one competition to the other.
PRIMARY_MODEL_COLUMNS = {
    "ucl": ("dc_home_win", "dc_draw", "dc_away_win"),
}


def main(league_id: str) -> None:
    odds_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_closing_odds.csv"
    hist_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    model_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    out_detail_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_backtest.csv"
    out_comparison_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_market_blend_comparison.csv"
    out_report_path = REPO_ROOT / "reports" / f"{league_id}_market_blend_report.md"

    odds_df = pd.read_csv(odds_path)
    hist_df = pd.read_csv(hist_path)[["match_id", "season", "date", "home_team", "away_team"]]
    model_df = pd.read_csv(model_path)

    odds_with_game = odds_df.merge(hist_df, on="match_id", how="inner")
    # backtest_continental_cup.py's own output has no match_id column,
    # only (date, home_team, away_team) -- join on that instead, same
    # discipline backtest_nba_market.py already established (no known
    # same-day same-pair collision within a single UCL/UEL season, but
    # dedup before merging anyway rather than trust that silently).
    model_dedup = model_df.drop_duplicates(subset=["date", "home_team", "away_team"], keep=False)
    model_dedup = model_dedup.drop(columns=["season"])  # keep hist_df's own season column, not a duplicate
    merged = odds_with_game.merge(model_dedup, on=["date", "home_team", "away_team"], how="inner")
    n_dropped = len(odds_with_game) - len(merged)
    if n_dropped:
        print(f"WARNING: {n_dropped}/{len(odds_with_game)} real odds rows had no matching real backtest row -- excluded, not estimated.")

    has_draw = merged["draw_moneyline_close"].notna() & (merged["draw_moneyline_close"] != "")
    n_no_draw = (~has_draw).sum()
    if n_no_draw:
        print(f"{n_no_draw} real games had no real draw line posted -- excluded, not estimated.")
    merged = merged[has_draw].copy()
    merged["draw_moneyline_close"] = merged["draw_moneyline_close"].astype(float)

    home_col, draw_col, away_col = PRIMARY_MODEL_COLUMNS[league_id]
    model_loss, blend_loss = [], []
    model_brier, blend_brier = [], []
    model_rps, blend_rps = [], []
    market_home, market_draw, market_away = [], [], []
    blend_home, blend_draw, blend_away = [], [], []

    for _, r in merged.iterrows():
        decimal_odds = (
            american_to_decimal(r["home_moneyline_close"]),
            american_to_decimal(r["draw_moneyline_close"]),
            american_to_decimal(r["away_moneyline_close"]),
        )
        mh, md, ma = remove_overround(decimal_odds)
        model_probs_tuple = (r[home_col], r[draw_col], r[away_col])
        bh, bd, ba = log_odds_average([model_probs_tuple, (mh, md, ma)])

        model_probs = {"home_win": r[home_col], "draw": r[draw_col], "away_win": r[away_col]}
        blend_probs = {"home_win": bh, "draw": bd, "away_win": ba}
        actual = r["actual_result"]

        market_home.append(mh); market_draw.append(md); market_away.append(ma)
        blend_home.append(bh); blend_draw.append(bd); blend_away.append(ba)
        model_loss.append(log_loss_row(model_probs, actual)); blend_loss.append(log_loss_row(blend_probs, actual))
        model_brier.append(brier_row(model_probs, actual)); blend_brier.append(brier_row(blend_probs, actual))
        model_rps.append(rps(model_probs, actual)); blend_rps.append(rps(blend_probs, actual))

    merged["market_home_win"], merged["market_draw"], merged["market_away_win"] = market_home, market_draw, market_away
    merged["blend_home_win"], merged["blend_draw"], merged["blend_away_win"] = blend_home, blend_draw, blend_away
    merged["model_log_loss"], merged["blend_log_loss"] = model_loss, blend_loss
    merged["model_brier"], merged["blend_brier"] = model_brier, blend_brier
    merged["model_rps"], merged["blend_rps"] = model_rps, blend_rps

    model_loss_arr, blend_loss_arr = np.array(model_loss), np.array(blend_loss)
    sig = paired_bootstrap_significance(model_loss_arr, blend_loss_arr, merged["season"].to_numpy())
    blend_significant = sig["ensemble_significant"]  # same ci-excludes-zero AND season-majority test, generic naming

    print(f"Real {league_id.upper()} model+market blend backtest on {len(merged)} real games "
          f"(primary model: {'Dixon-Coles' if home_col == 'dc_home_win' else 'Elo'}):")
    print(f"  Model-only mean log loss: {model_loss_arr.mean():.5f}")
    print(f"  Blend mean log loss:      {blend_loss_arr.mean():.5f}")
    print(f"  Bootstrap 95% CI on the edge: [{sig['ci_low']:+.5f}, {sig['ci_high']:+.5f}] "
          f"({sig['season_wins']}/{sig['n_seasons']} seasons)")
    print(f"  Blend significant: {blend_significant}")

    merged.to_csv(out_detail_path, index=False)
    pd.DataFrame([{
        "league_id": league_id, "n_matches": len(merged),
        "model_log_loss": round(float(model_loss_arr.mean()), 5), "blend_log_loss": round(float(blend_loss_arr.mean()), 5),
        "ci_low": round(sig["ci_low"], 5), "ci_high": round(sig["ci_high"], 5),
        "season_wins": sig["season_wins"], "n_seasons": sig["n_seasons"],
        "blend_significant": blend_significant, "generated_at": now_utc_iso(),
    }]).to_csv(out_comparison_path, index=False)

    with open(out_report_path, "w") as f:
        f.write(f"# {league_id.upper()} Model+Market Blend Report\n\n")
        f.write(
            f"**Genuinely thin -- read with real caution.** Only 2025-26 has a real collected ESPN "
            f"closing line for this competition (see collect_espn_continental_cup_odds.py), so this "
            f"backtest spans one real season and {len(merged)} real games, versus 2,660+ for a domestic "
            f"league's own market-blend backtest. The {sig['n_seasons']}-season breakdown below is "
            f"real, not a typo -- there is only one.\n\n"
        )
        f.write("## Model comparison (lower log loss is better)\n\n")
        f.write(f"| model | n_matches | log_loss | brier | rps |\n|---|---:|---:|---:|---:|\n")
        f.write(f"| Model-only ({'Dixon-Coles' if home_col == 'dc_home_win' else 'Elo'}) | {len(merged)} | "
                f"{model_loss_arr.mean():.4f} | {np.mean(model_brier):.4f} | {np.mean(model_rps):.4f} |\n")
        f.write(f"| Model + market blend | {len(merged)} | {blend_loss_arr.mean():.4f} | "
                f"{np.mean(blend_brier):.4f} | {np.mean(blend_rps):.4f} |\n\n")
        f.write(
            f"Paired bootstrap (10,000 resamples): point estimate "
            f"{sig['point_estimate']:+.4f} (positive = blend better), 95% CI "
            f"[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}]. Season wins: blend beats model-only in "
            f"{sig['season_wins']}/{sig['n_seasons']} season(s).\n\n"
            f"**Blend significantly better than model-only: {blend_significant}**\n"
        )
    print(f"Wrote {out_detail_path.name}, {out_comparison_path.name}, {out_report_path.name}")

    meta = make_run_metadata(prefix=f"market_blend_{league_id}", season="2026-27")
    log_experiment(meta, stage=f"market_blend_backtest_{league_id}", notes=(
        f"n_matches={len(merged)}, model_log_loss={model_loss_arr.mean():.4f}, "
        f"blend_log_loss={blend_loss_arr.mean():.4f}, significant={blend_significant}, "
        f"ci=[{sig['ci_low']:+.4f},{sig['ci_high']:+.4f}]"
    ))


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
