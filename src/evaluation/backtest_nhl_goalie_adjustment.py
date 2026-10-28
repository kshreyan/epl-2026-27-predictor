"""Real held-out-season test: does each team's real prior-season
primary goalie's GSAx (nhl_goalie_rating.py) explain real game outcomes
beyond what Elo-only (the real winner of NHL's own moneyline backtest
-- see backtest_team_sport.py) already captures? Fits a logistic
regression of the real outcome on [logit(Elo-only's own real
probability), goalie_diff] and checks whether the goalie_diff
coefficient's real bootstrap CI excludes zero -- never assumed to help.

Uses each team's PRIOR real season's primary-goalie rating to explain
the held-out season's real residual (a goalie's season-opening quality
is only knowable from games already played, same point-in-time
discipline as the QB test, at season granularity since that's the
real data this is built from -- see nhl_goalie_rating.py's own
disclosed scope limitation).

Run: python -m src.evaluation.backtest_nhl_goalie_adjustment
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logit
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection.collect_nhl_apiweb import RAW_NAME_BY_CODE  # noqa: E402
from src.models.nhl_goalie_rating import fetch_moneypuck_goalie_season, team_primary_goalie_gsax  # noqa: E402
from src.utils.team_names import normalize_team_name  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 20261028
NAME_BY_CODE = {code: normalize_team_name(name, league_id="nhl") for code, name in RAW_NAME_BY_CODE.items()}


def main(league_id: str = "nhl") -> None:
    backtest_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_match_results.csv"
    historical_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    model_df = pd.read_csv(backtest_path, parse_dates=["date"])
    hist_df = pd.read_csv(historical_path, parse_dates=["date"])

    seasons = sorted(int(s) for s in hist_df["season"].unique())
    held_out_season = seasons[-1]
    prior_season = held_out_season - 1

    print(f"Fetching real MoneyPuck goalie data for the prior real season ({prior_season})...")
    prior_goalies = fetch_moneypuck_goalie_season(prior_season)
    prior_ratings = team_primary_goalie_gsax(prior_goalies)
    team_gsax = {NAME_BY_CODE[code]: gsax for code, (gsax, _) in prior_ratings.items() if code in NAME_BY_CODE}

    held_out_games = hist_df[hist_df["season"] == held_out_season][["date", "home_team", "away_team"]]
    merged = model_df.merge(held_out_games, on=["date", "home_team", "away_team"], how="inner")
    merged["actual_home_win"] = (merged["actual_home_score"] > merged["actual_away_score"]).astype(int)
    merged["goalie_diff"] = merged.apply(
        lambda r: team_gsax.get(r["home_team"], 0.0) - team_gsax.get(r["away_team"], 0.0), axis=1,
    )
    merged["elo_logit"] = logit(np.clip(merged["elo_home_win"], 1e-6, 1 - 1e-6))

    n = len(merged)
    X = merged[["elo_logit", "goalie_diff"]].to_numpy()
    y = merged["actual_home_win"].to_numpy()
    model = LogisticRegression(C=np.inf).fit(X, y)
    coef = float(model.coef_[0][1])  # goalie_diff's own coefficient

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot_coefs = np.empty(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        boot_coefs[i] = LogisticRegression(C=np.inf).fit(X[idx], y[idx]).coef_[0][1]
    ci_low, ci_high = (float(x) for x in np.percentile(boot_coefs, [2.5, 97.5]))
    ci_excludes_zero = not (ci_low <= 0 <= ci_high)

    with_goalie_prob = model.predict_proba(X)[:, 1]
    with_goalie_loss = -np.mean(y * np.log(np.clip(with_goalie_prob, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - with_goalie_prob, 1e-12, 1)))
    elo_only_loss = -np.mean(y * np.log(np.clip(merged["elo_home_win"], 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - merged["elo_home_win"], 1e-12, 1)))

    print(f"Real held-out-season ({held_out_season}) goalie-adjustment test "
          f"(prior-season goalie ratings from real season {prior_season}, n={n} real games):")
    print(f"  Elo-only mean log loss:        {elo_only_loss:.5f}")
    print(f"  Elo + goalie-adjusted log loss: {with_goalie_loss:.5f}")
    print(f"  goalie_diff coefficient: {coef:.5f}, bootstrap 95% CI: [{ci_low:+.5f}, {ci_high:+.5f}]")
    print(f"  Significant: {ci_excludes_zero}")

    report_path = REPO_ROOT / "reports" / f"{league_id}_goalie_adjustment_report.md"
    with open(report_path, "w") as f:
        f.write(f"# {league_id.upper()} Goalie Adjustment Signal Report\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write(
            f"Real held-out-season test: each team's real prior-season ({prior_season}) primary goalie's real "
            f"shrunk GSAx (MoneyPuck) tested against real season {held_out_season}'s outcomes, on top of "
            f"Elo-only (this league's own real moneyline backtest winner). n={n} real games.\n\n"
            "**Real, disclosed scope limitation**: season-level goalie rating, not a live per-game confirmed-"
            "starter feature -- see nhl_goalie_rating.py's module docstring for why.\n\n"
        )
        f.write(f"- Elo-only mean log loss: {elo_only_loss:.5f}\n")
        f.write(f"- Elo + goalie-adjusted log loss: {with_goalie_loss:.5f}\n")
        f.write(f"- goalie_diff coefficient: {coef:.5f}\n")
        f.write(f"- Bootstrap 95% CI: [{ci_low:+.5f}, {ci_high:+.5f}]\n\n")
        verdict = (
            "**Significant** -- the real prior-season goalie signal explains real variance Elo-only misses; "
            "a real candidate to wire into live predictions."
            if ci_excludes_zero else
            "**No significant edge found.** The goalie adjustment is not wired into live predictions; "
            "Elo-only remains primary. A real, honest result -- a season-level, not live per-game confirmed-"
            "starter signal is a real, coarser proxy, and a richer live feature is a real candidate for a "
            "later phase, not assumed to arrive automatically."
        )
        f.write(f"## Verdict\n\n{verdict}\n")
    print(f"Wrote {report_path}")

    artifact_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_goalie_adjustment_coefficient.csv"
    pd.DataFrame([{
        "coefficient": round(coef, 5), "significant": ci_excludes_zero,
        "ci_low": round(ci_low, 5), "ci_high": round(ci_high, 5),
        "prior_season": prior_season, "held_out_season": held_out_season, "n_games": n,
        "generated_at": now_utc_iso(),
    }]).to_csv(artifact_path, index=False)
    print(f"Wrote {artifact_path}")


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default="nhl", dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
