"""Model+market blended prediction: a candidate evaluated against
Dixon-Coles alone with the exact same statistical bar the stacked
ensemble had to clear (final_stacked_model.py) -- built because a
review asked "will model+market be better than model alone", not
because it's assumed to help.

**The blend**: a 50/50 average of the model's probability and the
market's de-vigged probability, in log-odds space
(build_market_features.log_odds_average, already used and tested for
cross-bookmaker averaging -- reused here unchanged, just fed a
(model, market) pair instead of a (bookmaker, bookmaker) pair). No
blend weight is fit or tuned: an untuned 50/50 log-opinion-pool is the
standard default absent other information, and fitting a weight on
this sample would risk exactly the overfitting this project has
already been careful to avoid elsewhere (see recalibration_gate.py's
temperature-scaling-not-isotonic choice, same reasoning). Only ONE
candidate is tested, once -- not several weights compared post-hoc,
which would itself be a form of the leakage this project has spent
real effort catching in other places.

**Real historical market odds**, not synthetic: football-data.co.uk's
own closing "Avg" columns (the average closing price across every
bookmaker they track -- already cached locally from the original
historical-results collection, `data/external/football_data_co_uk/`,
no new network call). Full coverage confirmed across all 7 backtest
seasons: 2660/2660 matches, 2019/20-2025/26, 0 missing.

**Promotion bar**: identical to the ensemble's -- a paired bootstrap
(10,000 resamples) 95% CI on the log-loss difference (Dixon-Coles
minus market-blend) must exclude zero AND the challenger must win a
majority of the 7 backtest seasons. Anything less and Dixon-Coles
alone stays the answer in production, the same rule already applied
to the ensemble when it didn't clear this bar.

Run: python -m src.models.market_blend_model
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import RESULT_ORDER, brier_row, log_loss_row, rps  # noqa: E402
from src.features.build_market_features import log_odds_average, remove_overround  # noqa: E402
from src.models.final_stacked_model import N_BOOTSTRAP, BOOTSTRAP_SEED, paired_bootstrap_significance  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

BACKTEST_MATCH_RESULTS_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
RAW_CACHE_DIR = REPO_ROOT / "data" / "external" / "football_data_co_uk"
OUT_DETAIL = REPO_ROOT / "data" / "outputs" / "epl_market_blend_backtest.csv"
OUT_REPORT = REPO_ROOT / "reports" / "epl_2026_27_market_blend_report.md"

SEASON_CODES = {
    "2019-20": "1920", "2020-21": "2021", "2021-22": "2122", "2022-23": "2223",
    "2023-24": "2324", "2024-25": "2425", "2025-26": "2526",
}


def load_historical_market_odds(seasons: list[str]) -> pd.DataFrame:
    """Real closing-line no-vig probabilities for every match in the
    given seasons, keyed the same way backtest.py's elo_lookup already
    is (`YYYY-MM-DD_HomeTeam_AwayTeam`) so the two can be joined
    directly. Raises if a season's cached file or its Avg odds columns
    are missing -- never silently drops coverage."""
    rows = []
    for season in seasons:
        code = SEASON_CODES[season]
        path = RAW_CACHE_DIR / f"E0_{code}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No cached odds file for {season} at {path}")
        df = pd.read_csv(path)
        missing = df[["AvgH", "AvgD", "AvgA"]].isna().any(axis=1).sum()
        if missing:
            raise ValueError(f"{season}: {missing} matches missing Avg odds -- coverage is not actually complete")
        for _, row in df.iterrows():
            home = normalize_team_name(row["HomeTeam"])
            away = normalize_team_name(row["AwayTeam"])
            date_obj = pd.to_datetime(row["Date"], dayfirst=True)
            date_str = date_obj.strftime("%Y-%m-%d")
            h, d, a = remove_overround((float(row["AvgH"]), float(row["AvgD"]), float(row["AvgA"])))
            rows.append({
                "key": f"{date_str}_{home}_{away}", "season": season,
                "market_home_win": h, "market_draw": d, "market_away_win": a,
            })
    return pd.DataFrame(rows)


def evaluate_market_blend(results_df: pd.DataFrame | None = None) -> dict:
    """Reusable entry point for other modules (predict_all_matches.py):
    evaluates the 50/50 model+market log-odds blend against Dixon-Coles
    alone on real historical data, fresh every call (cheap -- no
    refitting, just a merge and 10,000 bootstrap resamples over ~2,660
    rows, well under a second). Returns whether the blend's edge is
    statistically significant (paired bootstrap CI excludes zero AND it
    wins a season majority -- the same bar the ensemble was held to)
    plus the comparison metrics and the merged per-match detail frame."""
    if results_df is None:
        if not BACKTEST_MATCH_RESULTS_PATH.exists():
            raise FileNotFoundError(f"{BACKTEST_MATCH_RESULTS_PATH} not found -- run the match-level backtest first.")
        results_df = pd.read_csv(BACKTEST_MATCH_RESULTS_PATH)
    results_df = results_df.copy()
    results_df["key"] = results_df["date"] + "_" + results_df["home_team"] + "_" + results_df["away_team"]

    seasons = sorted(results_df["season"].unique())
    market_odds = load_historical_market_odds(seasons)

    merged = results_df.merge(market_odds[["key", "market_home_win", "market_draw", "market_away_win"]], on="key", how="inner")
    n_dropped = len(results_df) - len(merged)
    if n_dropped:
        print(f"WARNING: {n_dropped}/{len(results_df)} backtest matches had no matching real market odds row -- excluded, not estimated.")

    blend_home, blend_draw, blend_away = [], [], []
    dc_loss, blend_loss = [], []
    dc_brier, blend_brier = [], []
    dc_rps, blend_rps = [], []

    for _, r in merged.iterrows():
        dc_probs = {"home_win": r["dc_home_win"], "draw": r["dc_draw"], "away_win": r["dc_away_win"]}
        market_probs_tuple = (r["market_home_win"], r["market_draw"], r["market_away_win"])
        dc_probs_tuple = (r["dc_home_win"], r["dc_draw"], r["dc_away_win"])
        bh, bd, ba = log_odds_average([dc_probs_tuple, market_probs_tuple])
        blend_probs = {"home_win": bh, "draw": bd, "away_win": ba}
        actual = r["actual_result"]

        blend_home.append(bh); blend_draw.append(bd); blend_away.append(ba)
        dc_loss.append(log_loss_row(dc_probs, actual)); blend_loss.append(log_loss_row(blend_probs, actual))
        dc_brier.append(brier_row(dc_probs, actual)); blend_brier.append(brier_row(blend_probs, actual))
        dc_rps.append(rps(dc_probs, actual)); blend_rps.append(rps(blend_probs, actual))

    merged["blend_home_win"] = blend_home
    merged["blend_draw"] = blend_draw
    merged["blend_away_win"] = blend_away
    merged["dc_log_loss_recomputed"] = dc_loss
    merged["blend_log_loss"] = blend_loss
    merged["dc_brier_recomputed"] = dc_brier
    merged["blend_brier"] = blend_brier
    merged["dc_rps_recomputed"] = dc_rps
    merged["blend_rps"] = blend_rps

    import numpy as np
    significance = paired_bootstrap_significance(
        np.array(dc_loss), np.array(blend_loss), merged["season"].to_numpy(),
        n_bootstrap=N_BOOTSTRAP, seed=BOOTSTRAP_SEED,
    )
    blend_significant = bool(significance["ci_excludes_zero"] and significance["season_majority"])

    return {
        "merged": merged, "n_matches": len(merged), "n_dropped": n_dropped, "n_total": len(results_df),
        "dc_mean_log_loss": float(np.mean(dc_loss)), "blend_mean_log_loss": float(np.mean(blend_loss)),
        "dc_mean_brier": float(np.mean(dc_brier)), "blend_mean_brier": float(np.mean(blend_brier)),
        "dc_mean_rps": float(np.mean(dc_rps)), "blend_mean_rps": float(np.mean(blend_rps)),
        "significance": significance, "blend_significant": blend_significant,
    }


def main() -> None:
    result = evaluate_market_blend()
    merged = result["merged"]
    n_dropped = result["n_dropped"]
    significance = result["significance"]
    blend_significant = result["blend_significant"]

    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    merged.drop(columns=["key"]).to_csv(OUT_DETAIL, index=False)

    dc_mean_ll = result["dc_mean_log_loss"]
    blend_mean_ll = result["blend_mean_log_loss"]
    dc_mean_brier = result["dc_mean_brier"]
    blend_mean_brier = result["blend_mean_brier"]
    dc_mean_rps = result["dc_mean_rps"]
    blend_mean_rps = result["blend_mean_rps"]

    print(f"Matches evaluated: {result['n_matches']}/{result['n_total']} ({n_dropped} dropped, no fabricated coverage)")
    print(f"Dixon-Coles alone: log loss {dc_mean_ll:.4f}, Brier {dc_mean_brier:.4f}, RPS {dc_mean_rps:.4f}")
    print(f"Model+market blend: log loss {blend_mean_ll:.4f}, Brier {blend_mean_brier:.4f}, RPS {blend_mean_rps:.4f}")
    print(f"Paired bootstrap ({N_BOOTSTRAP} resamples): point estimate {significance['point_estimate']:+.4f} "
          f"(positive = blend better), 95% CI [{significance['ci_low']:+.4f}, {significance['ci_high']:+.4f}]")
    print(f"Season wins: blend beats DC in {significance['season_wins']}/{significance['n_seasons']} seasons")
    print(f"Blend significantly better than Dixon-Coles alone: {blend_significant}")

    generated_at = now_utc_iso()
    with open(OUT_REPORT, "w") as f:
        f.write("# Model+Market Blend Backtest\n\n")
        f.write(f"Generated: {generated_at}\n\n")
        f.write(
            "Evaluates whether a 50/50 log-odds blend of the model's own probability and the "
            "real market's de-vigged probability beats Dixon-Coles alone, using the exact same "
            "paired-bootstrap promotion bar the stacked ensemble was held to (10,000 resamples, "
            "95% CI must exclude zero AND win a season majority). No blend weight is tuned -- "
            "an untuned 50/50 pool, tested once.\n\n"
        )
        f.write(f"**Real historical market odds**: football-data.co.uk closing \"Avg\" columns "
                f"(average across every bookmaker they track), {result['n_matches']}/{result['n_total']} backtest "
                f"matches matched ({n_dropped} dropped, not estimated).\n\n")
        f.write("## Headline numbers\n\n")
        f.write("| | Dixon-Coles alone | Model+market blend |\n|---|---|---|\n")
        f.write(f"| Log loss | {dc_mean_ll:.4f} | {blend_mean_ll:.4f} |\n")
        f.write(f"| Brier | {dc_mean_brier:.4f} | {blend_mean_brier:.4f} |\n")
        f.write(f"| RPS | {dc_mean_rps:.4f} | {blend_mean_rps:.4f} |\n\n")
        f.write(f"Paired bootstrap ({N_BOOTSTRAP} resamples): log-loss difference (DC - blend) "
                f"point estimate **{significance['point_estimate']:+.4f}** (positive favors the blend), "
                f"95% CI **[{significance['ci_low']:+.4f}, {significance['ci_high']:+.4f}]**.\n\n")
        f.write(significance["per_season"].to_string(index=False))
        f.write(f"\n\nBlend wins {significance['season_wins']}/{significance['n_seasons']} seasons.\n\n")
        if blend_significant:
            f.write("**The blend's edge is statistically significant (bootstrap CI excludes zero AND "
                    "it wins a season majority) -- promoted; live predictions use it for any fixture "
                    "with real market odds available, falling back to model-only otherwise.**\n")
        else:
            f.write("**The blend's edge is NOT statistically significant (bootstrap CI straddles zero "
                    "and/or it does not win a season majority) -- Dixon-Coles alone remains the "
                    "production model for every fixture, market data available or not.**\n")

    meta = make_run_metadata(
        prefix="market_blend", season="2026-27", calibration_method="none",
        latest_source_timestamp_used=generated_at,
    )
    log_experiment(
        meta, stage="market_blend_backtest",
        notes=f"n_matches={len(merged)}, blend_log_loss={blend_mean_ll:.4f}, dc_log_loss={dc_mean_ll:.4f}, "
              f"significant={blend_significant}, ci=[{significance['ci_low']:+.4f},{significance['ci_high']:+.4f}]",
    )
    print(f"\nReport written to {OUT_REPORT}")
    return blend_significant


if __name__ == "__main__":
    main()
