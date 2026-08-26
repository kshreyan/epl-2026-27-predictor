"""Model+market blended predictions for the two derived betting markets
that have a real historical market baseline -- Asian Handicap (spread)
and Over/Under 2.5 goals (totals) -- evaluated against the model-only
Dixon-Coles derivation with the exact same statistical bar every other
blend/ensemble candidate in this project has been held to
(final_stacked_model.paired_bootstrap_significance, reused unchanged
here as it was for market_blend_model.py's moneyline blend).

**Why this is a separate module from market_blend_model.py**: that one
blends three-outcome (1X2) probabilities; these two are binary markets
(cover/not-cover, over/under), which need a different de-vig/log-odds-
average shape (`remove_overround_binary`/`log_odds_average_binary` in
build_market_features.py) and a different real-data source column set.
Sharing one module would have meant branching on market shape inside
almost every function -- clearer to keep 1X2 and binary-market blending
as parallel, independently-readable modules.

**BTTS has no real market baseline anywhere** (The Odds API returns
`INVALID_MARKET` for `btts` on this sport; football-data.co.uk's cached
files have no BTTS column) -- confirmed directly, not assumed. There is
therefore nothing to validate a BTTS blend against; it stays
model-only, by design, not because this was skipped.

**Real historical odds**: football-data.co.uk's closing-line averages,
already cached (`data/external/football_data_co_uk/E0_*.csv`):
- Spread: `AHh` (the consensus closing handicap line, home-team-signed)
  with `AvgAHH`/`AvgAHA` (average decimal odds for the home/away side
  covering that same line).
- Totals: `Avg>2.5`/`Avg<2.5` (average decimal odds for the fixed 2.5
  line -- the market convention `total_goals_probabilities` already
  matches via `DEFAULT_TOTAL_GOALS_LINE`).

**The model's own probability for each real historical match** is
derived from `data/outputs/epl_backtest_match_results.csv`'s
`dc_lambda`/`dc_mu`/`dc_rho` columns (added specifically for this) by
reconstructing the exact scoreline matrix (`score_matrix`) that the
walk-forward backtest already fit for that match -- no re-fitting, and
no approximation from the top-10 scorelines list.

**Blend**: an untuned 50/50 log-odds average of the model's probability
and the market's de-vigged probability (`log_odds_average_binary`) --
same non-tuning discipline as the moneyline blend, for the same reason
(fitting a weight on this sample would be a form of leakage this
project has been careful to avoid elsewhere).

Run: python -m src.models.spread_totals_blend_model
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.features.build_market_features import log_odds_average_binary, remove_overround_binary  # noqa: E402
from src.models.final_stacked_model import N_BOOTSTRAP, BOOTSTRAP_SEED, paired_bootstrap_significance  # noqa: E402
from src.models.scoreline_models import (  # noqa: E402
    asian_handicap_home_cover_probability,
    score_matrix,
    total_goals_probabilities,
)
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

DEFAULT_TOTAL_GOALS_LINE = 2.5  # matches predict_all_matches.py's constant of the same name

BACKTEST_MATCH_RESULTS_PATH = REPO_ROOT / "data" / "outputs" / "epl_backtest_match_results.csv"
RAW_CACHE_DIR = REPO_ROOT / "data" / "external" / "football_data_co_uk"
OUT_DETAIL = REPO_ROOT / "data" / "outputs" / "epl_spread_totals_blend_backtest.csv"
OUT_REPORT = REPO_ROOT / "reports" / "epl_2026_27_spread_totals_blend_report.md"

SEASON_CODES = {
    "2019-20": "1920", "2020-21": "2021", "2021-22": "2122", "2022-23": "2223",
    "2023-24": "2324", "2024-25": "2425", "2025-26": "2526",
}


def _binary_log_loss(p: float, outcome: float) -> float:
    """outcome is 1.0 (covered/over), 0.0 (didn't), or 0.5 (a push on a
    whole-number handicap line -- scored as the average of the two
    possible binary log losses, since a push is genuinely half a cover
    rather than a real third outcome)."""
    if outcome == 0.5:
        return -0.5 * (np.log(max(p, 1e-12)) + np.log(max(1 - p, 1e-12)))
    q = p if outcome == 1.0 else 1.0 - p
    return -np.log(max(q, 1e-12))


def load_historical_spread_totals_odds(seasons: list[str]) -> pd.DataFrame:
    """Real closing-line Asian Handicap line/odds and Over/Under 2.5
    odds for every match in the given seasons, keyed the same way
    market_blend_model.load_historical_market_odds is. Rows missing
    either market's real columns are dropped, not estimated -- reported
    to the caller via the row count difference, matching the moneyline
    blend's own "never fabricate coverage" discipline."""
    rows = []
    for season in seasons:
        code = SEASON_CODES[season]
        path = RAW_CACHE_DIR / f"E0_{code}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No cached odds file for {season} at {path}")
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            home = normalize_team_name(row["HomeTeam"])
            away = normalize_team_name(row["AwayTeam"])
            date_obj = pd.to_datetime(row["Date"], dayfirst=True)
            date_str = date_obj.strftime("%Y-%m-%d")
            out = {"key": f"{date_str}_{home}_{away}", "season": season}

            ah_line, ah_h, ah_a = row.get("AHh"), row.get("AvgAHH"), row.get("AvgAHA")
            if pd.notna(ah_line) and pd.notna(ah_h) and pd.notna(ah_a):
                market_home_cover, _ = remove_overround_binary((float(ah_h), float(ah_a)))
                out["market_ah_line"] = float(ah_line)
                out["market_home_cover"] = market_home_cover
            else:
                out["market_ah_line"] = None
                out["market_home_cover"] = None

            over_odds, under_odds = row.get("Avg>2.5"), row.get("Avg<2.5")
            if pd.notna(over_odds) and pd.notna(under_odds):
                market_over, _ = remove_overround_binary((float(over_odds), float(under_odds)))
                out["market_over_2_5"] = market_over
            else:
                out["market_over_2_5"] = None

            rows.append(out)
    return pd.DataFrame(rows)


def evaluate_spread_totals_blends(results_df: pd.DataFrame | None = None) -> dict:
    """Reusable entry point (predict_all_matches.py): evaluates both the
    spread and totals 50/50 model+market log-odds blends against
    model-only Dixon-Coles on real historical data. Returns whether
    each blend's edge is statistically significant (paired bootstrap CI
    excludes zero AND wins a season majority) plus comparison metrics
    and per-match detail."""
    if results_df is None:
        if not BACKTEST_MATCH_RESULTS_PATH.exists():
            raise FileNotFoundError(f"{BACKTEST_MATCH_RESULTS_PATH} not found -- run the match-level backtest first.")
        results_df = pd.read_csv(BACKTEST_MATCH_RESULTS_PATH)
    missing_lam = {"dc_lambda", "dc_mu", "dc_rho"} - set(results_df.columns)
    if missing_lam:
        raise ValueError(
            f"{BACKTEST_MATCH_RESULTS_PATH} is missing {missing_lam} -- re-run "
            "`python -m src.evaluation.backtest` (backtest.py now stores these for exactly this use)."
        )
    results_df = results_df.copy()
    results_df["key"] = results_df["date"] + "_" + results_df["home_team"] + "_" + results_df["away_team"]

    seasons = sorted(results_df["season"].unique())
    odds = load_historical_spread_totals_odds(seasons)
    merged = results_df.merge(odds, on="key", how="inner", suffixes=("", "_odds"))
    n_total = len(results_df)

    out = {}
    for market_name, real_line_col, real_prob_col, model_fn_desc in [
        ("spread", "market_ah_line", "market_home_cover", "asian_handicap_home_cover_probability"),
        ("totals", None, "market_over_2_5", "total_goals_probabilities"),
    ]:
        avail = merged[merged[real_prob_col].notna()].copy()
        if market_name == "spread":
            avail = avail[avail[real_line_col].notna()]
        n_dropped = n_total - len(avail)

        model_probs, market_probs, blend_probs = [], [], []
        outcomes = []
        for _, r in avail.iterrows():
            matrix = score_matrix(float(r["dc_lambda"]), float(r["dc_mu"]), float(r["dc_rho"]))
            actual_total = int(r["actual_home_goals"]) + int(r["actual_away_goals"])
            if market_name == "spread":
                line = float(r["market_ah_line"])
                model_p = asian_handicap_home_cover_probability(matrix, line)
                actual_diff = int(r["actual_home_goals"]) - int(r["actual_away_goals"]) + line
                # A push (whole-number line, diff exactly 0) is scored as a
                # 0.5 "outcome" via the same log-loss formula generalized to
                # a fractional target -- matches how the model's own cover
                # probability already treats a push as half a cover.
                if abs(actual_diff) < 1e-9:
                    outcome = 0.5
                else:
                    outcome = 1.0 if actual_diff > 0 else 0.0
            else:
                model_p, _ = total_goals_probabilities(matrix, DEFAULT_TOTAL_GOALS_LINE)
                outcome = 1.0 if actual_total > DEFAULT_TOTAL_GOALS_LINE else 0.0
            market_p = float(r[real_prob_col])
            blend_p = log_odds_average_binary([model_p, market_p])
            model_probs.append(model_p); market_probs.append(market_p); blend_probs.append(blend_p)
            outcomes.append(outcome)

        outcomes_arr = np.array(outcomes)
        model_loss = np.array([_binary_log_loss(p, o) for p, o in zip(model_probs, outcomes_arr)])
        blend_loss = np.array([_binary_log_loss(p, o) for p, o in zip(blend_probs, outcomes_arr)])

        significance = paired_bootstrap_significance(
            model_loss, blend_loss, avail["season"].to_numpy(), n_bootstrap=N_BOOTSTRAP, seed=BOOTSTRAP_SEED,
        )
        blend_significant = bool(significance["ci_excludes_zero"] and significance["season_majority"])

        detail = avail[["season", "date", "home_team", "away_team"]].copy()
        detail["model_prob"] = model_probs
        detail["market_prob"] = market_probs
        detail["blend_prob"] = blend_probs
        detail["outcome"] = outcomes_arr
        detail["model_log_loss"] = model_loss
        detail["blend_log_loss"] = blend_loss

        out[market_name] = {
            "detail": detail, "n_matches": len(avail), "n_dropped": n_dropped, "n_total": n_total,
            "model_mean_log_loss": float(model_loss.mean()), "blend_mean_log_loss": float(blend_loss.mean()),
            "significance": significance, "blend_significant": blend_significant,
        }
    return out


def main() -> None:
    result = evaluate_spread_totals_blends()
    generated_at = now_utc_iso()

    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    combined = []
    for market_name, r in result.items():
        d = r["detail"].copy()
        d.insert(0, "market", market_name)
        combined.append(d)
    pd.concat(combined, ignore_index=True).to_csv(OUT_DETAIL, index=False)

    lines = ["# Spread (Asian Handicap) and Totals (Over/Under 2.5) Market Blend Backtest\n",
              f"Generated: {generated_at}\n",
              "Evaluates whether a 50/50 log-odds blend of the model's own probability and the real "
              "market's de-vigged probability beats model-only Dixon-Coles, using the same paired-bootstrap "
              "promotion bar the moneyline blend and stacked ensemble were held to (10,000 resamples, 95% CI "
              "must exclude zero AND win a season majority). No blend weight is tuned.\n"]

    for market_name, label in [("spread", "Asian Handicap (spread)"), ("totals", "Over/Under 2.5 (totals)")]:
        r = result[market_name]
        sig = r["significance"]
        print(f"[{market_name}] {r['n_matches']}/{r['n_total']} matches evaluated ({r['n_dropped']} dropped, "
              f"no real market line/odds -- not estimated)")
        print(f"[{market_name}] Model-only log loss {r['model_mean_log_loss']:.4f}, "
              f"blend log loss {r['blend_mean_log_loss']:.4f}")
        print(f"[{market_name}] Paired bootstrap: point estimate {sig['point_estimate']:+.4f} "
              f"(positive = blend better), 95% CI [{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], "
              f"season wins {sig['season_wins']}/{sig['n_seasons']}")
        print(f"[{market_name}] Blend significantly better: {r['blend_significant']}")

        lines.append(f"\n## {label}\n")
        lines.append(f"**Real historical market odds**: football-data.co.uk closing averages, "
                      f"{r['n_matches']}/{r['n_total']} backtest matches matched ({r['n_dropped']} dropped, not estimated).\n")
        lines.append("| | Model-only | Model+market blend |\n|---|---|---|\n")
        lines.append(f"| Log loss | {r['model_mean_log_loss']:.4f} | {r['blend_mean_log_loss']:.4f} |\n")
        lines.append(f"\nPaired bootstrap ({N_BOOTSTRAP} resamples): log-loss difference (model - blend) "
                      f"point estimate **{sig['point_estimate']:+.4f}** (positive favors the blend), "
                      f"95% CI **[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}]**.\n")
        lines.append(f"\n{sig['per_season'].to_string(index=False)}\n")
        lines.append(f"\nBlend wins {sig['season_wins']}/{sig['n_seasons']} seasons.\n")
        if r["blend_significant"]:
            lines.append(f"\n**The {label} blend's edge is statistically significant -- promoted; live predictions "
                          f"use it for any fixture with a real market line/odds for this market, falling back to "
                          f"model-only otherwise.**\n")
        else:
            lines.append(f"\n**The {label} blend's edge is NOT statistically significant -- model-only remains the "
                          f"production prediction for this market, real market data available or not.**\n")

    with open(OUT_REPORT, "w") as f:
        f.write("".join(lines))

    meta = make_run_metadata(prefix="spread_totals_blend", season="2026-27", calibration_method="none",
                              latest_source_timestamp_used=generated_at)
    log_experiment(
        meta, stage="spread_totals_blend_backtest",
        notes=(f"spread: n={result['spread']['n_matches']}, significant={result['spread']['blend_significant']}; "
               f"totals: n={result['totals']['n_matches']}, significant={result['totals']['blend_significant']}"),
    )
    print(f"\nReport written to {OUT_REPORT}")
    return {k: v["blend_significant"] for k, v in result.items()}


if __name__ == "__main__":
    main()
