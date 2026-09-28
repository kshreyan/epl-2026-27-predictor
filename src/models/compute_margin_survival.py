"""Margin Survival / +2 Asian Handicap engine -- second-stage tail
modeling on top of the existing Dixon-Coles scoreline predictor.

Scope (Phase 1, real-data-only): the 5 domestic leagues that have a
real, backtested Dixon-Coles fit (2,660+ historical matches each). MLS
and UEFA Nations League are deliberately excluded -- their own
moneyline models are Elo-only because Dixon-Coles was found to badly
overfit on their much smaller real backtest samples (see
reports/nations_league_model_selection_report.md and the MLS backtest
report); running a margin-tail model on top of an already-flagged
"less validated" scoreline surface would manufacture false precision,
which this module explicitly must not do.

This does NOT reduce to "predicted score is close, therefore safe" --
that would be circular (see module docstring in the master prompt this
implements). Every match gets its FULL Dixon-Coles score matrix
recomputed (not just the top-1 predicted score), and every margin
bucket (win/draw/lose-1/lose-2/lose-3/lose-4+) is read directly off
that real, already-backtested joint distribution. The eligibility
filter (central prediction is 0-1, 1-0, or any draw) only decides which
matches are interesting enough to publish -- it is not treated as the
tail estimate itself.

No fabricated inputs: this module does NOT model lineups or in-game
tactical resilience (no real per-match feed for either exists in this
project -- see PREDICTION_COLUMNS' injury_data_available/
lineup_data_available, always False). Those two factors from the
master prompt's spec are intentionally omitted rather than faked. The
"rotation/incentive" factor uses the real schedule-congestion features
(build_schedule_congestion_features) instead.

Run: python -m src.models.compute_margin_survival [--league epl]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.features.build_schedule_congestion_features import build_schedule_congestion_features  # noqa: E402
from src.models.predict_all_matches import _paths, build_model_context  # noqa: E402
from src.models.promoted_team_adjustment import derive_promoted_teams  # noqa: E402
from src.models.scoreline_models import match_lambdas, score_matrix  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

MARGIN_SURVIVAL_LEAGUE_IDS = ["epl", "la_liga", "serie_a", "bundesliga", "ligue_1"]
ELIGIBLE_DRAWS_AND = {(0, 1), (1, 0)}
LOOKBACK_MATCHES = 38  # ~1 real season per team, time-ordered, no leakage (strictly before as_of_date)
MIN_HISTORY_MATCHES = 10  # below this, historical-tail factor is withheld rather than computed on a thin sample

RISK_LABELS = [
    (0.04, "ELITE +2 SURVIVAL"),
    (0.06, "VERY STRONG"),
    (0.09, "STRONG"),
    (0.14, "MODERATE"),
    (float("inf"), "HIGH BLOWOUT RISK"),
]

OUTPUT_COLUMNS = [
    "match_id", "league_id", "season", "matchweek", "date", "kickoff_utc", "status",
    "team", "opponent", "is_home", "predicted_score_model_only", "eligible",
    "win_prob", "draw_prob", "lose_1_prob", "lose_2_prob", "lose_3_prob", "lose_4plus_prob",
    "p_cover", "p_push", "p_fail", "p_survive", "risk_label",
    "factor_strength_gap_score", "factor_low_total_score",
    "factor_historical_tail_score", "factor_opponent_blowout_score", "factor_rotation_score",
    "team_history_n_matches", "team_history_loss3plus_rate",
    "opponent_history_n_matches", "opponent_history_win3plus_rate",
    "why_text", "run_id", "model_version", "generated_at",
]


def risk_label(p_fail: float) -> str:
    for threshold, label in RISK_LABELS:
        if p_fail < threshold:
            return label
    return RISK_LABELS[-1][1]


def margin_buckets(matrix: np.ndarray, perspective: str) -> dict:
    """perspective='home' or 'away' -- which side's goal difference to bucket."""
    n = matrix.shape[0]
    win = draw = lose1 = lose2 = lose3 = lose4p = 0.0
    for i in range(n):
        for j in range(n):
            p = matrix[i, j]
            gd = (i - j) if perspective == "home" else (j - i)
            if gd > 0:
                win += p
            elif gd == 0:
                draw += p
            elif gd == -1:
                lose1 += p
            elif gd == -2:
                lose2 += p
            elif gd == -3:
                lose3 += p
            else:
                lose4p += p
    return {"win": win, "draw": draw, "lose_1": lose1, "lose_2": lose2, "lose_3": lose3, "lose_4plus": lose4p}


def team_recent_matches(df_clean: pd.DataFrame, team: str, as_of_date: pd.Timestamp) -> pd.DataFrame:
    m = df_clean[((df_clean["home_team"] == team) | (df_clean["away_team"] == team)) & (df_clean["date"] < as_of_date)]
    return m.sort_values("date").tail(LOOKBACK_MATCHES)


def team_loss3plus_rate(df_clean: pd.DataFrame, team: str, as_of_date: pd.Timestamp) -> tuple[float | None, int]:
    """Real share of this team's own recent matches lost by a 3+ goal margin."""
    m = team_recent_matches(df_clean, team, as_of_date)
    if len(m) < MIN_HISTORY_MATCHES:
        return None, len(m)
    gd = np.where(m["home_team"] == team, m["home_goals"] - m["away_goals"], m["away_goals"] - m["home_goals"])
    return float((gd <= -3).mean()), len(m)


def team_win3plus_rate(df_clean: pd.DataFrame, team: str, as_of_date: pd.Timestamp) -> tuple[float | None, int]:
    """Real share of this team's own recent matches WON by a 3+ goal margin -- the opponent's blowout-generation rate."""
    m = team_recent_matches(df_clean, team, as_of_date)
    if len(m) < MIN_HISTORY_MATCHES:
        return None, len(m)
    gd = np.where(m["home_team"] == team, m["home_goals"] - m["away_goals"], m["away_goals"] - m["home_goals"])
    return float((gd >= 3).mean()), len(m)


def percentile_score(value: float, reference: list[float], favorable_low: bool) -> float:
    """0-10 score from where `value` sits in `reference`'s real empirical
    distribution -- favorable_low=True means a LOW value is favorable
    (e.g. a small total-goal environment, or a low historical
    blowout-loss rate)."""
    if not reference:
        return 5.0
    pct = float(np.mean([v <= value for v in reference]))  # fraction of reference at or below value
    score = (1 - pct) if favorable_low else pct
    return round(score * 10, 1)


def why_text(team: str, opponent: str, is_home: bool, lam: float, mu: float, p_fail: float,
             team_tail_rate: float | None, team_tail_n: int,
             opp_blowout_rate: float | None, opp_blowout_n: int,
             rotation_note: str | None) -> str:
    total_goals = lam + mu
    total_desc = "low" if total_goals < 2.4 else ("moderate" if total_goals < 3.0 else "elevated")
    win_prob_gap = abs((lam - mu))
    gap_desc = "small" if win_prob_gap < 0.3 else ("moderate" if win_prob_gap < 0.8 else "large")
    parts = [
        f"Projected total-goal environment is {total_desc} ({total_goals:.2f} expected goals combined), "
        f"and the modeled attacking gap between {team} and {opponent} is {gap_desc} "
        f"({lam:.2f} vs {mu:.2f} expected goals)."
    ]
    if team_tail_rate is not None:
        parts.append(f"{team} lost by 3+ in {team_tail_rate:.0%} of its last {team_tail_n} real matches.")
    else:
        parts.append(f"{team}'s recent-history sample ({team_tail_n} matches) is too thin to score reliably.")
    if opp_blowout_rate is not None:
        parts.append(f"{opponent} won by 3+ in {opp_blowout_rate:.0%} of its last {opp_blowout_n} real matches.")
    else:
        parts.append(f"{opponent}'s recent-history sample ({opp_blowout_n} matches) is too thin to score reliably.")
    if rotation_note:
        parts.append(rotation_note)
    parts.append(f"Net modeled probability of a 3+ goal defeat: {p_fail:.1%}.")
    return " ".join(parts)


def compute_for_league(league_id: str) -> pd.DataFrame:
    paths = _paths(league_id)
    with open(paths["model_config"]) as f:
        model_cfg = yaml.safe_load(f)

    df = pd.read_csv(paths["historical"], parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    fixtures_df = pd.read_csv(paths["fixtures"])
    congestion_df = build_schedule_congestion_features(fixtures_df)
    fixtures_df = fixtures_df.merge(congestion_df, on="match_id", how="left")

    preds_df = pd.read_csv(paths["out_predictions"])
    teams_2627 = sorted(set(fixtures_df["home_team"]) | set(fixtures_df["away_team"]))
    promoted_teams = derive_promoted_teams(teams_2627, df_clean)
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(teams_2627))

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    ctx = build_model_context(
        df_clean, universe, model_cfg, as_of_date, promoted_teams=promoted_teams,
        league_id=league_id, backtest_path=paths["backtest"], active_calibrators_path=paths["active_calibrators"],
    )
    fit = ctx["fit"]

    meta = make_run_metadata(prefix="margin_survival", season="2026-27")
    generated_at = now_utc_iso()

    fx_by_id = fixtures_df.set_index("match_id")
    pred_by_id = preds_df.set_index("match_id")

    # Reference distributions for percentile-based factor scores: computed
    # once per league from every fixture's real lam/mu, not per-match, so
    # a single match's own score can't distort its own baseline.
    all_totals: list[float] = []
    all_gaps: list[float] = []
    fixture_matrices: dict[str, tuple[float, float, np.ndarray]] = {}
    for match_id, fx in fx_by_id.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        if home not in fit.team_index or away not in fit.team_index:
            continue
        lam, mu = match_lambdas(fit, home, away)
        matrix = score_matrix(lam, mu, fit.rho)
        fixture_matrices[match_id] = (lam, mu, matrix)
        all_totals.append(lam + mu)
        all_gaps.append(abs(lam - mu))

    rows = []
    for match_id, (lam, mu, matrix) in fixture_matrices.items():
        fx = fx_by_id.loc[match_id]
        pred = pred_by_id.loc[match_id] if match_id in pred_by_id.index else None
        predicted_score = pred["predicted_score_model_only"] if pred is not None else None
        eligible = False
        if isinstance(predicted_score, str) and "-" in predicted_score:
            h, a = (int(x) for x in predicted_score.split("-"))
            eligible = (h, a) in ELIGIBLE_DRAWS_AND or h == a

        for is_home, team, opponent in ((True, fx["home_team"], fx["away_team"]), (False, fx["away_team"], fx["home_team"])):
            perspective = "home" if is_home else "away"
            buckets = margin_buckets(matrix, perspective)
            p_cover = buckets["win"] + buckets["draw"] + buckets["lose_1"]
            p_push = buckets["lose_2"]
            p_fail = buckets["lose_3"] + buckets["lose_4plus"]

            team_tail_rate, team_tail_n = team_loss3plus_rate(df_clean, team, as_of_date)
            opp_blowout_rate, opp_blowout_n = team_win3plus_rate(df_clean, opponent, as_of_date)

            rest_diff = fx.get("rest_day_diff")
            cong_diff = fx.get("congestion_diff")
            opponent_is_more_congested = None
            rotation_note = None
            if pd.notna(cong_diff):
                # cong_diff is home-minus-away matches in the last 7 days;
                # flip sign when `team` is away so it always reads as
                # "opponent's own congestion minus team's".
                opp_relative_congestion = -cong_diff if is_home else cong_diff
                opponent_is_more_congested = opp_relative_congestion > 0
                if opponent_is_more_congested:
                    rotation_note = f"{opponent} has a heavier recent fixture schedule than {team}, a real (if modest) rotation/fatigue signal."
                elif opp_relative_congestion < 0:
                    rotation_note = f"{team} has a heavier recent fixture schedule than {opponent} -- a real (if modest) fatigue risk works against this pick."

            factor_strength_gap = percentile_score(abs(lam - mu), all_gaps, favorable_low=True)
            factor_low_total = percentile_score(lam + mu, all_totals, favorable_low=True)
            factor_hist_tail = None if team_tail_rate is None else round((1 - team_tail_rate) * 10, 1)
            factor_opp_blowout = round((1 - opp_blowout_rate) * 10, 1) if opp_blowout_rate is not None else None
            factor_rotation = (
                None if opponent_is_more_congested is None
                else (7.0 if opponent_is_more_congested else 3.0)
            )

            rows.append({
                "match_id": match_id, "league_id": league_id, "season": fx["season"], "matchweek": fx["matchweek"],
                "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "status": fx["status"],
                "team": team, "opponent": opponent, "is_home": is_home,
                "predicted_score_model_only": predicted_score, "eligible": eligible,
                "win_prob": round(buckets["win"], 4), "draw_prob": round(buckets["draw"], 4),
                "lose_1_prob": round(buckets["lose_1"], 4), "lose_2_prob": round(buckets["lose_2"], 4),
                "lose_3_prob": round(buckets["lose_3"], 4), "lose_4plus_prob": round(buckets["lose_4plus"], 4),
                "p_cover": round(p_cover, 4), "p_push": round(p_push, 4), "p_fail": round(p_fail, 4),
                "p_survive": round(p_cover + p_push, 4), "risk_label": risk_label(p_fail),
                "factor_strength_gap_score": factor_strength_gap, "factor_low_total_score": factor_low_total,
                "factor_historical_tail_score": factor_hist_tail, "factor_opponent_blowout_score": factor_opp_blowout,
                "factor_rotation_score": factor_rotation,
                "team_history_n_matches": team_tail_n, "team_history_loss3plus_rate": team_tail_rate,
                "opponent_history_n_matches": opp_blowout_n, "opponent_history_win3plus_rate": opp_blowout_rate,
                "why_text": why_text(team, opponent, is_home, lam, mu, p_fail, team_tail_rate, team_tail_n,
                                      opp_blowout_rate, opp_blowout_n, rotation_note),
                "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
            })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_2026_27_margin_survival.csv"
    out_df.to_csv(out_path, index=False)
    n_eligible = int(out_df["eligible"].sum())
    print(f"Wrote {len(out_df)} margin-survival rows ({n_eligible} eligible-team rows) to {out_path}")
    log_experiment(meta, stage="compute_margin_survival", notes=f"{league_id}: {n_eligible} eligible-team rows of {len(out_df)}")
    return out_df


def main(league_id: str | None = None) -> None:
    league_ids = [league_id] if league_id else MARGIN_SURVIVAL_LEAGUE_IDS
    for lid in league_ids:
        compute_for_league(lid)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", default=None, dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
