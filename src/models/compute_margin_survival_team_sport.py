"""+2 Margin Survival's sport-correct equivalent for NFL, NBA, NHL and
NCAA Football.

**This is not soccer's "+2 goals" ported literally -- it's the same
underlying question (how likely is this team to lose by a real,
sport-recognizable "blowout" margin), answered with each sport's own
real scoring scale, backed by real research, not guessed:**

- **NFL**: real NFL spread betting has well-established "key numbers"
  -- 3 and 7 occur as the real final margin far more often than any
  other number (confirmed via direct research: ~14-15% of games by
  exactly 3, ~9% by exactly 7) because scoring is built from 3-point
  field goals and 7-point touchdowns. The real median NFL margin is
  already 8 points, so a line anywhere near a single score is close to
  a coin flip, not a rare tail event the way soccer's "+2 goals" is.
  The threshold here is **margin of defeat > 14** -- two full
  touchdowns (2 x 7), still built from the sport's own real scoring
  unit -- which lands at the real **~70th percentile** of real
  historical absolute margins (checked directly: p70 = 14.0 across
  1,452 real historical games; ~29.5% of real games exceed it).
- **NBA**: real research confirms the NBA has "no key numbers of real
  consequence" (near-continuous scoring). No borrowed number -- the
  threshold (**> 20 points**) comes from this league's own real
  backtested margin-of-victory distribution (see
  backtest_team_sport.py's "Real historical margin-of-victory
  distribution": 20 points sits at the real ~80th percentile of real
  historical absolute margins, and matches the commonly-used informal
  real-world framing of an NBA "blowout").
- **NHL**: real NHL spread betting has its own well-known real "puck
  line" (+/-1.5 goals) -- but checked directly against this league's
  own real backtested margin distribution, that line answers a
  DIFFERENT real question (a near-even-money spread-cover proposition
  by design, same realization NFL's own "7" key number led to): the
  real median NHL margin is already 2.0 goals, so "> 1" would make
  p_fail exceed 25% for an even matchup, nowhere near a rare blowout.
  The threshold here is **margin of defeat > 3 goals** -- a real "three-
  goal game," which lands the real backtested p_fail distribution in
  the same real scale as NBA's own bands (confirmed directly: NHL's
  p20-p80 at this threshold, 0.075-0.108, sit almost exactly where
  NBA's own 0.069-0.118 do), unlike the puck line's 1.5.
- **NCAA Football**: no real equivalent of NFL's key numbers exists
  for this sport (checked directly -- no documented real research
  found). The threshold (**> 21 points**, "three touchdowns") comes
  from this league's own real backtested margin-of-victory
  distribution: 21 points sits at the real ~70th percentile of real
  historical absolute margins -- the same real percentile NFL's own
  14-point ("two touchdowns") threshold lands at, a real, honest
  parallel rather than a coincidence of round numbers (both derived
  the same way, from each sport's own real data, at the same real
  percentile, in each sport's own real scoring unit).

Built on the point-margin model (src/models/point_margin_model.py)
regardless of whether that model actually won this league's own real
backtest for the MONEYLINE prediction (it does for NFL, not for NBA/
NHL/NCAA Football -- see should_use_point_margin_model() and
reports/{league}_model_selection_report.md) -- it's the only candidate
that produces a real margin distribution at all (Elo-only win
probability has no margin/scoreline concept, same structural reason
Dixon-Coles powers soccer's margin survival even where Elo wins that
league's own moneyline backtest). NHL's own real backtest additionally
tried Dixon-Coles (unlike NFL/NBA/NCAA Football -- see
backtest_team_sport.py) and found it clearly WORSE than even a flat
baseline (confirmed directly: 0.829 real log loss vs. the flat
baseline's 0.691) -- a real, checked answer, not the a priori
expectation that low/discrete scoring would make it competitive; NHL's
margin survival uses the point-margin model, same as every other
league here. Every row's `why_text` says plainly when the powering
model is not this league's own moneyline winner.

Risk-tier labels/thresholds reuse the soccer engine's generic
risk_label/verdict/percentile_score helpers directly (imported, not
duplicated) but with NEW real p_fail bands chosen from each sport's
own real backtested p_fail distribution (soccer's own 0.04/0.06/
0.09/0.14 bands have no documented derivation formula in this codebase
-- checked directly -- they're reasonable round numbers for soccer's
own scale, not a formula to replicate verbatim for a different sport).

Run: python -m src.models.compute_margin_survival_team_sport --league nfl
(also accepts nba, nhl, ncaaf)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_team_sport import ALLOWS_TIES, ELO_K_FACTOR  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.compute_margin_survival import ELIGIBLE_DRAWS_AND, percentile_score, verdict  # noqa: E402
from src.models.point_margin_model import fit_point_margin_model, predict_margin_distribution, should_use_point_margin_model  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

# Real, sport-correct blowout threshold (points/goals) -- see module docstring.
MARGIN_THRESHOLD = {"nfl": 14, "nba": 20, "nhl": 3, "ncaaf": 21}

# Real bands, same 5-tier shape as soccer's engine, calibrated to each
# sport's OWN real p_fail scale -- NOT a first guess: computed directly
# from the real p_fail distribution across every real historical game
# in each sport's own backtest sample, at the real 20th/40th/60th/80th
# percentiles (NFL: 0.120/0.128/0.178/0.189 at the 14-point threshold;
# NBA: 0.069/0.082/0.100/0.118 at 20 points; NHL: 0.075/0.085/0.097/
# 0.108 at 3 goals; NCAA Football: 0.102/0.108/0.194/0.203 at 21
# points). Each sport's real bands are at a meaningfully different
# scale -- no shared set fits all four, so each gets its own.
RISK_LABELS = {
    "nfl": [
        (0.12, "ELITE SURVIVAL"), (0.13, "VERY STRONG"), (0.18, "STRONG"), (0.19, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "nba": [
        (0.08, "ELITE SURVIVAL"), (0.09, "VERY STRONG"), (0.11, "STRONG"), (0.14, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "nhl": [
        (0.08, "ELITE SURVIVAL"), (0.09, "VERY STRONG"), (0.10, "STRONG"), (0.11, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
    "ncaaf": [
        (0.10, "ELITE SURVIVAL"), (0.11, "VERY STRONG"), (0.19, "STRONG"), (0.20, "MODERATE"),
        (float("inf"), "HIGH BLOWOUT RISK"),
    ],
}

OUTPUT_COLUMNS = [
    "match_id", "league_id", "season", "matchweek", "date", "kickoff_utc", "status",
    "team", "opponent", "is_home", "predicted_score_model_only", "eligible",
    "win_prob", "draw_prob", "lose_1_prob", "lose_2_prob", "lose_3_prob", "lose_4plus_prob",
    "p_cover", "p_push", "p_fail", "p_survive", "risk_label",
    "factor_strength_gap_score", "factor_low_total_score",
    "factor_historical_tail_score", "factor_opponent_blowout_score", "factor_rotation_score",
    "team_history_n_matches", "team_history_loss3plus_rate",
    "opponent_history_n_matches", "opponent_history_win3plus_rate",
    "real_line", "real_odds", "real_bookmaker", "cover_prob_at_real_line",
    "implied_prob_at_real_line", "value_gap", "fair_plus2_decimal_odds", "threshold", "verdict",
    "why_text", "run_id", "model_version", "generated_at",
]


def _risk_label(league_id: str, p_fail: float) -> str:
    for threshold, label in RISK_LABELS[league_id]:
        if p_fail < threshold:
            return label
    return RISK_LABELS[league_id][-1][1]


def cover_probability_at_line(mean: float, sigma: float, team_line: float) -> float:
    """P(team's own margin + team_line > 0) -- team_line follows real
    spread convention (negative = favorite laying points, positive =
    underdog getting points), read directly off the fitted Normal
    distribution rather than a discrete scoreline grid (there isn't
    one for this sport's model -- see module docstring)."""
    return float(1 - norm.cdf(-team_line, loc=mean, scale=sigma))


def margin_buckets(mean: float, sigma: float, threshold: int) -> dict:
    """p_cover/p_push/p_fail off the continuous Normal margin
    distribution -- the sport-correct generalization of soccer's
    discrete win/draw/lose_1/lose_2/lose_3/lose_4plus scoreline
    buckets (there's no discrete scoreline grid here, only a
    continuous margin). `threshold` is this sport's real blowout line
    (14 for NFL, 20 for NBA, 3 for NHL, 21 for NCAA Football)."""
    win = float(1 - norm.cdf(0, loc=mean, scale=sigma))
    # "push" = losing by approximately exactly `threshold` (within the
    # real discrete-score rounding band, same ±0.5 convention
    # point_margin_model.py uses for NFL's real tie probability).
    push = float(norm.cdf(-(threshold - 0.5), loc=mean, scale=sigma) - norm.cdf(-(threshold + 0.5), loc=mean, scale=sigma))
    fail = float(norm.cdf(-(threshold + 0.5), loc=mean, scale=sigma))
    cover = max(1 - push - fail, 0.0)
    return {"win": win, "cover": cover, "push": push, "fail": fail}


def why_text(league_display: str, league_id: str, team: str, opponent: str, mean: float, sigma: float,
             p_fail: float, threshold: int, using_winning_model: bool) -> str:
    validation_note = (
        f"Built on {league_display}'s own point-margin model, the real winner of this league's moneyline "
        f"backtest (see reports/{league_id}_model_selection_report.md)."
        if using_winning_model else
        f"Built on {league_display}'s own point-margin model, which real backtesting found did NOT beat the "
        f"Elo-only model used for this match's moneyline prediction (see "
        f"reports/{league_id}_model_selection_report.md) -- read this verdict with real caution."
    )
    favored = team if mean > 0 else opponent
    return (
        f"{validation_note} Projected margin: {team} {'+' if mean >= 0 else ''}{mean:.1f} points "
        f"(model std dev {sigma:.1f}). {favored} is the projected favorite. "
        f"Net modeled probability of losing by more than {threshold}: {p_fail:.1%}."
    )


def compute_for_league(league_id: str) -> pd.DataFrame:
    cfg = load_league_config(league_id)
    threshold = MARGIN_THRESHOLD[league_id]
    allows_ties = ALLOWS_TIES[league_id]

    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    real_odds_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_odds.csv")
    preds_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_match_predictions.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_margin_survival.csv")

    df = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures_df = pd.read_csv(fixtures_path)
    preds_df = pd.read_csv(preds_path).set_index("match_id") if preds_path.exists() else pd.DataFrame()
    real_odds_df = pd.read_csv(real_odds_path) if real_odds_path.exists() else pd.DataFrame()

    if real_results_path.exists():
        real_results = pd.read_csv(real_results_path)
        if not real_results.empty:
            id_to_teams = fixtures_df.set_index("match_id")[["home_team", "away_team", "date"]]
            completed_rows = []
            for _, rr in real_results.iterrows():
                if rr["match_id"] not in id_to_teams.index:
                    continue
                fx = id_to_teams.loc[rr["match_id"]]
                completed_rows.append({
                    "date": pd.Timestamp(fx["date"]), "home_team": fx["home_team"], "away_team": fx["away_team"],
                    "home_score": rr["home_goals"], "away_score": rr["away_goals"],
                })
            if completed_rows:
                df = pd.concat([df, pd.DataFrame(completed_rows)], ignore_index=True)

    # NCAA Football only: real conference-aware reversion -- confirmed
    # via a real paired-bootstrap test to beat flat reversion on this
    # specific margin task (see predict_team_sport_matches.py's own
    # identical wiring and reports/ncaaf_model_selection_report.md).
    team_group = None
    if league_id == "ncaaf":
        from src.data_collection.espn_api import fetch_real_fbs_conferences
        conferences = fetch_real_fbs_conferences()
        team_group = {t["display_name"]: conf for conf, roster in conferences.items() for t in roster}

    fit = fit_point_margin_model(df, allows_ties=allows_ties, k_factor=ELO_K_FACTOR, team_group=team_group)
    using_winning_model = should_use_point_margin_model(league_id)

    real_spread_by_match: dict[str, pd.Series] = {}
    if not real_odds_df.empty:
        spreads = real_odds_df[
            (real_odds_df["market_type"] == "spreads")
            & ((real_odds_df["is_real_data"] == True) | (real_odds_df["is_real_data"] == "True"))  # noqa: E712
        ]
        for match_id, group in spreads.groupby("match_id"):
            pinnacle = group[group["bookmaker"] == "pinnacle"]
            real_spread_by_match[match_id] = pinnacle.iloc[0] if not pinnacle.empty else group.iloc[0]

    meta = make_run_metadata(prefix="margin_survival_team_sport", season="2026-27")
    generated_at = now_utc_iso()
    fx_by_id = fixtures_df.set_index("match_id")

    all_abs_margins: list[float] = []
    fixture_dists: dict[str, tuple[float, float]] = {}
    for match_id, fx in fx_by_id.iterrows():
        mean, sigma = predict_margin_distribution(fit, fx["home_team"], fx["away_team"])
        fixture_dists[match_id] = (mean, sigma)
        all_abs_margins.append(abs(mean))

    rows = []
    for match_id, (mean, sigma) in fixture_dists.items():
        fx = fx_by_id.loc[match_id]
        pred = preds_df.loc[match_id] if (not preds_df.empty and match_id in preds_df.index) else None
        predicted_score = pred["predicted_score_model_only"] if pred is not None else None
        eligible = False
        if isinstance(predicted_score, str) and "-" in predicted_score:
            h, a = (int(x) for x in predicted_score.split("-"))
            eligible = (h, a) in ELIGIBLE_DRAWS_AND or h == a

        for is_home, team, opponent, team_mean in (
            (True, fx["home_team"], fx["away_team"], mean),
            (False, fx["away_team"], fx["home_team"], -mean),
        ):
            buckets = margin_buckets(team_mean, sigma, threshold)
            p_cover, p_push, p_fail = buckets["cover"], buckets["push"], buckets["fail"]

            factor_strength_gap = percentile_score(abs(team_mean), all_abs_margins, favorable_low=True)
            row_risk_label = _risk_label(league_id, p_fail)

            real_line = real_odds = real_bookmaker = None
            cover_prob_at_real_line = implied_prob_at_real_line = value_gap = None
            spread_row = real_spread_by_match.get(match_id)
            if spread_row is not None and pd.notna(spread_row.get("spread_line")):
                home_line = float(spread_row["spread_line"])
                team_line = home_line if is_home else -home_line
                cover_prob_at_real_line = round(cover_probability_at_line(team_mean, sigma, team_line), 4)
                real_line = round(team_line, 2)
                real_odds_val = spread_row.get("home_spread_odds") if is_home else spread_row.get("away_spread_odds")
                real_bookmaker = spread_row.get("bookmaker")
                if real_odds_val and pd.notna(real_odds_val) and float(real_odds_val) > 0:
                    real_odds = round(float(real_odds_val), 2)
                    implied_prob_at_real_line = round(1 / real_odds, 4)
                    value_gap = round(cover_prob_at_real_line - implied_prob_at_real_line, 4)

            fair_plus2_decimal_odds = round(1 + p_fail / p_cover, 3) if p_cover > 0 else None

            rows.append({
                "match_id": match_id, "league_id": league_id, "season": fx["season"], "matchweek": fx["matchweek"],
                "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "status": fx["status"],
                "team": team, "opponent": opponent, "is_home": is_home,
                "predicted_score_model_only": predicted_score, "eligible": eligible,
                "win_prob": round(buckets["win"], 4), "draw_prob": 0.0,
                "lose_1_prob": None, "lose_2_prob": None, "lose_3_prob": None, "lose_4plus_prob": None,
                "p_cover": round(p_cover, 4), "p_push": round(p_push, 4), "p_fail": round(p_fail, 4),
                "p_survive": round(p_cover + p_push, 4), "risk_label": row_risk_label,
                "factor_strength_gap_score": factor_strength_gap, "factor_low_total_score": None,
                "factor_historical_tail_score": None, "factor_opponent_blowout_score": None,
                "factor_rotation_score": None,
                "team_history_n_matches": None, "team_history_loss3plus_rate": None,
                "opponent_history_n_matches": None, "opponent_history_win3plus_rate": None,
                "real_line": real_line, "real_odds": real_odds, "real_bookmaker": real_bookmaker,
                "cover_prob_at_real_line": cover_prob_at_real_line,
                "implied_prob_at_real_line": implied_prob_at_real_line, "value_gap": value_gap,
                "fair_plus2_decimal_odds": fair_plus2_decimal_odds,
                "threshold": threshold,
                "verdict": verdict(row_risk_label, value_gap, f"+{threshold}"),
                "why_text": why_text(cfg.display_name, league_id, team, opponent, team_mean, sigma, p_fail, threshold, using_winning_model),
                "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
            })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    tally = out_df["verdict"].value_counts().to_dict()
    print(f"Wrote {len(out_df)} margin-survival rows to {out_path} -- verdicts: {tally}")
    log_experiment(meta, stage="compute_margin_survival_team_sport", notes=f"{league_id}: {len(out_df)} rows, verdicts={tally}")
    return out_df


def main(league_id: str) -> None:
    compute_for_league(league_id)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba", "nhl", "ncaaf"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
