"""+2 Margin Survival for a UEFA club competition (UCL, UEL, UECL).

**Read this before trusting these numbers as much as the 5 domestic
leagues' own +2 Margin Survival.** The real backtest
(src/evaluation/backtest_continental_cup.py) found Elo clearly beats
Dixon-Coles for all three competitions' moneyline prediction -- the
same reasoning that made the old, now-removed compute_margin_survival.py
exclude MLS and Nations League outright ("running a margin-tail model
on top of an already-flagged less-validated scoreline surface would
manufacture false precision"). This module runs anyway, on explicit
request, using the competition's own separately-fit Dixon-Coles score
matrix (real matrix, real backtest, just the weaker of the two real
models tested) -- every row's `why_text` says so plainly, and so does
the field `moneyline_model_source` is compared against in
reports/{league}_model_selection_report.md. Treat verdicts here as
less trustworthy than a domestic league's.

Deliberately NOT built on top of the domestic predict_all_matches.py /
build_model_context pipeline (which the original compute_margin_
survival.py imports): that pipeline hard-requires a `promoted_teams`
argument with no continental-cup equivalent, gates isotonic calibration
at a real 500-match minimum none of these three competitions clear,
and runs ensemble-significance machinery with nothing to ensemble
against here. Reuses the same low-level primitives directly
(scoreline_models.match_lambdas/score_matrix) and the same bucket/
verdict/factor logic as the domestic engine (imported from
compute_margin_survival.py, not duplicated), fit directly from
fit_dixon_coles_model on each competition's own real historical pool --
the same approach backtest_continental_cup.py already validated.

No schedule-congestion/rotation factor (factor_rotation_score is always
null): build_schedule_congestion_features assumes a single domestic
calendar; no equivalent exists for a continental competition whose
clubs each also play a full, different domestic season in parallel.

Run: python -m src.models.compute_margin_survival_continental --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest_continental_cup import HALF_LIFE_DAYS, L2_REG  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.compute_margin_survival import (  # noqa: E402
    ELIGIBLE_DRAWS_AND,
    OUTPUT_COLUMNS,
    THRESHOLD,
    margin_buckets,
    percentile_score,
    risk_label,
    team_loss3plus_rate,
    team_win3plus_rate,
    verdict,
)
from src.models.scoreline_models import asian_handicap_home_cover_probability, fit_dixon_coles_model, match_lambdas, score_matrix  # noqa: E402
from src.utils.versioning import MODEL_VERSION, log_experiment, make_run_metadata, now_utc_iso  # noqa: E402

LESS_VALIDATED_NOTE = (
    "Built on {league}'s own separately-fit Dixon-Coles scoreline model, which real backtesting found "
    "clearly weaker than the Elo model used for this match's moneyline prediction (see "
    "reports/{league_id}_model_selection_report.md) -- read this verdict with real caution."
)


def why_text_continental(league_display: str, league_id: str, team: str, opponent: str, lam: float, mu: float, p_fail: float,
                          team_tail_rate: float | None, team_tail_n: int,
                          opp_blowout_rate: float | None, opp_blowout_n: int) -> str:
    total_goals = lam + mu
    total_desc = "low" if total_goals < 2.4 else ("moderate" if total_goals < 3.0 else "elevated")
    win_prob_gap = abs(lam - mu)
    gap_desc = "small" if win_prob_gap < 0.3 else ("moderate" if win_prob_gap < 0.8 else "large")
    parts = [
        LESS_VALIDATED_NOTE.format(league=league_display, league_id=league_id),
        f"Projected total-goal environment is {total_desc} ({total_goals:.2f} expected goals combined), "
        f"and the modeled attacking gap between {team} and {opponent} is {gap_desc} "
        f"({lam:.2f} vs {mu:.2f} expected goals).",
    ]
    if team_tail_rate is not None:
        parts.append(f"{team} lost by 3+ in {team_tail_rate:.0%} of its last {team_tail_n} real matches.")
    else:
        parts.append(f"{team}'s recent-history sample ({team_tail_n} matches) is too thin to score reliably.")
    if opp_blowout_rate is not None:
        parts.append(f"{opponent} won by 3+ in {opp_blowout_rate:.0%} of its last {opp_blowout_n} real matches.")
    else:
        parts.append(f"{opponent}'s recent-history sample ({opp_blowout_n} matches) is too thin to score reliably.")
    parts.append(f"Net modeled probability of a 3+ goal defeat: {p_fail:.1%}.")
    return " ".join(parts)


def compute_for_league(league_id: str) -> pd.DataFrame:
    cfg = load_league_config(league_id)
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    real_odds_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_odds.csv")
    preds_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_match_predictions.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_margin_survival.csv")

    df = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures_df = pd.read_csv(fixtures_path)
    preds_df = pd.read_csv(preds_path).set_index("match_id")
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
                    "home_goals": rr["home_goals"], "away_goals": rr["away_goals"],
                })
            if completed_rows:
                df = pd.concat([df, pd.DataFrame(completed_rows)], ignore_index=True)

    teams_2627 = sorted(set(fixtures_df["home_team"]) | set(fixtures_df["away_team"]))
    universe = sorted(set(df["home_team"]) | set(df["away_team"]) | set(teams_2627))

    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    fit = fit_dixon_coles_model(df, universe, as_of_date, half_life_days=HALF_LIFE_DAYS, l2_reg=L2_REG)

    real_spread_by_match: dict[str, pd.Series] = {}
    if not real_odds_df.empty:
        spreads = real_odds_df[
            (real_odds_df["market_type"] == "spreads")
            & ((real_odds_df["is_real_data"] == True) | (real_odds_df["is_real_data"] == "True"))  # noqa: E712
        ]
        for match_id, group in spreads.groupby("match_id"):
            pinnacle = group[group["bookmaker"] == "pinnacle"]
            real_spread_by_match[match_id] = pinnacle.iloc[0] if not pinnacle.empty else group.iloc[0]

    meta = make_run_metadata(prefix="margin_survival_continental", season="2026-27")
    generated_at = now_utc_iso()

    fx_by_id = fixtures_df.set_index("match_id")

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
        pred = preds_df.loc[match_id] if match_id in preds_df.index else None
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

            team_tail_rate, team_tail_n = team_loss3plus_rate(df, team, as_of_date)
            opp_blowout_rate, opp_blowout_n = team_win3plus_rate(df, opponent, as_of_date)

            factor_strength_gap = percentile_score(abs(lam - mu), all_gaps, favorable_low=True)
            factor_low_total = percentile_score(lam + mu, all_totals, favorable_low=True)
            factor_hist_tail = None if team_tail_rate is None else round((1 - team_tail_rate) * 10, 1)
            factor_opp_blowout = round((1 - opp_blowout_rate) * 10, 1) if opp_blowout_rate is not None else None

            real_line = real_odds = real_bookmaker = None
            cover_prob_at_real_line = implied_prob_at_real_line = value_gap = None
            spread_row = real_spread_by_match.get(match_id)
            if spread_row is not None and pd.notna(spread_row.get("spread_line")):
                home_line = float(spread_row["spread_line"])
                home_cover = asian_handicap_home_cover_probability(matrix, home_line)
                cover_prob_at_real_line = round(home_cover if is_home else (1 - home_cover), 4)
                real_line = round(home_line if is_home else -home_line, 2)
                real_odds_val = spread_row.get("home_spread_odds") if is_home else spread_row.get("away_spread_odds")
                real_bookmaker = spread_row.get("bookmaker")
                if real_odds_val and pd.notna(real_odds_val) and float(real_odds_val) > 0:
                    real_odds = round(float(real_odds_val), 2)
                    implied_prob_at_real_line = round(1 / real_odds, 4)
                    value_gap = round(cover_prob_at_real_line - implied_prob_at_real_line, 4)

            fair_plus2_decimal_odds = round(1 + p_fail / p_cover, 3) if p_cover > 0 else None
            row_risk_label = risk_label(p_fail)

            rows.append({
                "match_id": match_id, "league_id": league_id, "season": fx["season"], "matchweek": fx["matchweek"],
                "date": fx["date"], "kickoff_utc": fx["kickoff_utc"], "status": fx["status"],
                "team": team, "opponent": opponent, "is_home": is_home,
                "predicted_score_model_only": predicted_score, "eligible": eligible,
                "win_prob": round(buckets["win"], 4), "draw_prob": round(buckets["draw"], 4),
                "lose_1_prob": round(buckets["lose_1"], 4), "lose_2_prob": round(buckets["lose_2"], 4),
                "lose_3_prob": round(buckets["lose_3"], 4), "lose_4plus_prob": round(buckets["lose_4plus"], 4),
                "p_cover": round(p_cover, 4), "p_push": round(p_push, 4), "p_fail": round(p_fail, 4),
                "p_survive": round(p_cover + p_push, 4), "risk_label": row_risk_label,
                "factor_strength_gap_score": factor_strength_gap, "factor_low_total_score": factor_low_total,
                "factor_historical_tail_score": factor_hist_tail, "factor_opponent_blowout_score": factor_opp_blowout,
                "factor_rotation_score": None,
                "team_history_n_matches": team_tail_n, "team_history_loss3plus_rate": team_tail_rate,
                "opponent_history_n_matches": opp_blowout_n, "opponent_history_win3plus_rate": opp_blowout_rate,
                "real_line": real_line, "real_odds": real_odds, "real_bookmaker": real_bookmaker,
                "cover_prob_at_real_line": cover_prob_at_real_line,
                "implied_prob_at_real_line": implied_prob_at_real_line, "value_gap": value_gap,
                "fair_plus2_decimal_odds": fair_plus2_decimal_odds,
                "threshold": THRESHOLD,
                "verdict": verdict(row_risk_label, value_gap, THRESHOLD),
                "why_text": why_text_continental(cfg.display_name, league_id, team, opponent, lam, mu, p_fail,
                                                  team_tail_rate, team_tail_n, opp_blowout_rate, opp_blowout_n),
                "run_id": meta.run_id, "model_version": MODEL_VERSION, "generated_at": generated_at,
            })

    out_df = pd.DataFrame(rows)[OUTPUT_COLUMNS]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    tally = out_df["verdict"].value_counts().to_dict()
    print(f"Wrote {len(out_df)} margin-survival rows to {out_path} -- verdicts: {tally}")
    log_experiment(meta, stage="compute_margin_survival_continental", notes=f"{league_id}: {len(out_df)} rows, verdicts={tally}")
    return out_df


def main(league_id: str) -> None:
    compute_for_league(league_id)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
