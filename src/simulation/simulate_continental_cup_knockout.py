"""Monte Carlo simulation of a UEFA club competition's FULL remaining
season -- the rest of the 36-team league phase, then the real
knockout bracket (playoff round -> Round of 16 -> quarter-finals ->
semi-finals -> Final) -- all the way to who wins the competition.

**Read this before trusting these numbers at all.** Built on explicit
request despite every real constraint that made this out of scope
before: the league phase is only partially complete (most remaining
fixtures are genuinely unplayed), the real knockout bracket does not
exist yet (no draw has happened), and this is new, NOT independently
backtested simulation code layering several already-flagged-as-less-
validated pieces on top of each other:

1. Remaining league-phase results: match WIN/DRAW/LOSS is drawn from
   each team's current Elo rating (the real, backtested, primary
   moneyline model -- see reports/{league}_model_selection_report.md),
   seeded from real domestic-league Elo where this competition's own
   backtest found that helps (see cross_competition_elo.py). Elo
   ratings are held FIXED at today's value for every simulated
   trial -- unlike simulate_full_season.py's domestic Dixon-Coles
   simulation, which draws a fresh attack/defense value per trial from
   each team's real fitted uncertainty, this does NOT propagate rating
   uncertainty. Probabilities here are therefore sharper/more
   confident than the real uncertainty actually supports, especially
   this early in the league phase.
2. Scorelines (needed for goal-difference tiebreaks and 2-legged
   knockout AGGREGATE scoring -- Elo alone gives no scoreline) are
   drawn from the Simple-Poisson model, CONDITIONED on the result Elo
   already drew for that match (so "who wins" stays governed by the
   validated model; only the goal margin, a secondary figure, comes
   from the separately-fit, NOT independently backtested-for-margins
   Simple-Poisson surface).
3. Knockout draws (playoff round: ranks 9-16 seeded vs 17-24
   unseeded; Round of 16: ranks 1-8 seeded vs the 8 playoff winners
   unseeded; quarter-finals/semi-finals: fully open, no seeding, no
   same-association protection -- all real UEFA rules, confirmed
   directly, not assumed) are drawn uniformly at random within those
   real constraints, independently per trial.
4. A 2-legged tie level on aggregate after both legs is resolved by a
   50/50 coin flip. This pipeline has no real extra-time/penalty-
   shootout model, and inventing team-specific penalty-taking ability
   from no real data would be fabrication -- 50/50 is the honest
   "no information" choice, not a precisely-estimated figure.

Output is per-team probabilities of: finishing in the real direct-
Round-of-16 zone (top 8), the real play-off zone (9th-24th), real
league-phase elimination (25th-36th), reaching each knockout round,
and winning the competition outright. Treat all of this as a rough
directional guide, not a precise forecast -- re-run as the season
progresses and these numbers will sharpen for real as more of the
season's actual uncertainty resolves.

Run: python -m src.simulation.simulate_continental_cup_knockout --league ucl
(also accepts uel, uecl)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.evaluation.backtest import team_rolling_goal_avgs  # noqa: E402
from src.evaluation.backtest_continental_cup import ELO_HOME_ADVANTAGE, ELO_K_FACTOR  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.baselines import elo_only_probabilities, simple_poisson_baseline  # noqa: E402
from src.models.cross_competition_elo import cross_competition_seed_ratings, should_use_domestic_seed  # noqa: E402
from src.models.elo_model import run_elo  # noqa: E402
from src.models.scoreline_models import score_matrix  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

N_TRIALS = 5000
RNG_SEED = 20261019  # fixed seed -- reproducible trial-to-trial, not re-randomized on every re-run
MAX_GOALS = 8  # matches score_matrix's grid (0..8 each side)


def result_from_score(hg: int, ag: int) -> str:
    if hg > ag:
        return "home_win"
    if hg < ag:
        return "away_win"
    return "draw"


def draw_match(rng: np.random.Generator, r_home: float, r_away: float, lam: float, mu: float) -> tuple[str, int, int]:
    """Draws (result, home_goals, away_goals) for one match: result from
    Elo (validated), scoreline from Simple-Poisson conditioned on that
    result (see module docstring)."""
    home_win, draw, away_win = elo_only_probabilities(r_home, r_away, ELO_HOME_ADVANTAGE)
    result = rng.choice(["home_win", "draw", "away_win"], p=[home_win, draw, away_win])

    matrix = score_matrix(lam, mu, rho=0.0)
    idx = np.indices(matrix.shape)
    if result == "home_win":
        mask = idx[0] > idx[1]
    elif result == "away_win":
        mask = idx[0] < idx[1]
    else:
        mask = idx[0] == idx[1]
    weights = matrix[mask]
    total = weights.sum()
    if total <= 0:
        # Degenerate (e.g. an extreme lam/mu puts ~0 mass on this result
        # class) -- fall back to the nearest valid scoreline for that
        # class rather than crashing or dividing by zero.
        hg, ag = (1, 0) if result == "home_win" else ((0, 1) if result == "away_win" else (0, 0))
        return result, hg, ag
    weights = weights / total
    cells = np.argwhere(mask)
    choice_idx = rng.choice(len(cells), p=weights)
    hg, ag = cells[choice_idx]
    return result, int(hg), int(ag)


def simulate_two_legged_tie(rng: np.random.Generator, team_a: str, team_b: str,
                             ratings: dict[str, float], lam_mu: dict[str, tuple[float, float]]) -> str:
    """team_a hosts leg 1, team_b hosts leg 2 (real UEFA convention: the
    lower-ranked/unseeded side in these three competitions' knockout
    phase hosts the first leg). Returns the winner."""
    r_a, r_b = ratings.get(team_a, 1500.0), ratings.get(team_b, 1500.0)
    lam_a, mu_a = lam_mu.get(team_a, (1.3, 1.1))
    lam_b, mu_b = lam_mu.get(team_b, (1.3, 1.1))

    _, a_leg1_gf, a_leg1_ga = draw_match(rng, r_a, r_b, lam_a, mu_b)
    _, b_leg2_gf, b_leg2_ga = draw_match(rng, r_b, r_a, lam_b, mu_a)

    agg_a = a_leg1_gf + b_leg2_ga
    agg_b = a_leg1_ga + b_leg2_gf
    if agg_a > agg_b:
        return team_a
    if agg_b > agg_a:
        return team_b
    return team_a if rng.random() < 0.5 else team_b


def draw_knockout_round(rng: np.random.Generator, seeded: list[str], unseeded: list[str],
                         ratings: dict[str, float], lam_mu: dict[str, tuple[float, float]]) -> list[str]:
    """Real UEFA draw: each seeded team is paired with a uniformly-random
    unseeded team (no same-association protection in these three
    competitions as of 2025-26 -- confirmed directly), unseeded team
    hosts leg 1. Returns the round's winners."""
    shuffled_unseeded = rng.permutation(unseeded).tolist()
    winners = []
    for seed, opponent in zip(seeded, shuffled_unseeded):
        winners.append(simulate_two_legged_tie(rng, opponent, seed, ratings, lam_mu))
    return winners


def draw_open_round(rng: np.random.Generator, teams: list[str],
                     ratings: dict[str, float], lam_mu: dict[str, tuple[float, float]]) -> list[str]:
    """Quarter-finals/semi-finals: fully open draw, no seeding, no
    same-association protection (confirmed directly). Pairing order
    (who hosts leg 1) is uniformly random -- real home-leg-order
    advantage rules (top-ranked sides hosting the second leg) are a
    minor real detail not modeled here."""
    shuffled = rng.permutation(teams).tolist()
    winners = []
    for i in range(0, len(shuffled), 2):
        a, b = shuffled[i], shuffled[i + 1]
        winners.append(simulate_two_legged_tie(rng, a, b, ratings, lam_mu))
    return winners


def main(league_id: str) -> None:
    cfg = load_league_config(league_id)
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_knockout_probabilities.csv")

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures = pd.read_csv(fixtures_path)
    real_results = pd.read_csv(real_results_path) if real_results_path.exists() else pd.DataFrame(columns=["match_id", "home_goals", "away_goals"])
    results_by_id = real_results.set_index("match_id") if not real_results.empty else real_results

    teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    n_teams = len(teams)
    assert n_teams == cfg.n_teams, f"{league_id}: expected {cfg.n_teams} teams, found {n_teams}"

    completed_rows = []
    base_points = {t: 0 for t in teams}
    base_gf = {t: 0 for t in teams}
    base_ga = {t: 0 for t in teams}
    remaining_fixtures = []
    for _, fx in fixtures.iterrows():
        if fx["match_id"] in results_by_id.index:
            rr = results_by_id.loc[fx["match_id"]]
            hg, ag = int(rr["home_goals"]), int(rr["away_goals"])
            home, away = fx["home_team"], fx["away_team"]
            base_gf[home] += hg; base_ga[home] += ag
            base_gf[away] += ag; base_ga[away] += hg
            if hg > ag:
                base_points[home] += 3
            elif hg < ag:
                base_points[away] += 3
            else:
                base_points[home] += 1; base_points[away] += 1
            completed_rows.append({
                "date": pd.Timestamp(fx["date"]), "home_team": home, "away_team": away,
                "home_goals": hg, "away_goals": ag,
            })
        else:
            remaining_fixtures.append((fx["home_team"], fx["away_team"]))

    if completed_rows:
        historical = pd.concat([historical, pd.DataFrame(completed_rows)], ignore_index=True)

    # Cross-competition Elo seed (see cross_competition_elo.py) only
    # when this competition's own real backtest found it helps -- same
    # conditional predict_continental_cup_matches.py uses, read fresh
    # from the same backtest comparison CSV rather than duplicated/
    # assumed here.
    seed_ratings = cross_competition_seed_ratings() if should_use_domestic_seed(league_id) else None
    elo_run = run_elo(historical, seed_ratings=seed_ratings, k_factor=ELO_K_FACTOR, home_advantage=ELO_HOME_ADVANTAGE)
    ratings = elo_run.final_ratings
    league_avg_goals = float(pd.concat([historical["home_goals"], historical["away_goals"]]).mean())

    # Each team's own (lam, mu) vs a league-average opponent -- used only
    # to approximate a GENERIC goal-scoring rate for knockout legs where
    # the specific opponent's rolling goal average needs a real baseline;
    # match_lambdas-equivalent per real opponent is computed fresh inside
    # draw_match/simulate_two_legged_tie wherever the specific pairing is
    # known (remaining league-phase fixtures); this per-team dict instead
    # backstops the knockout rounds, whose opponents aren't known until a
    # trial's own draw happens.
    team_lam_mu: dict[str, tuple[float, float]] = {}
    for t in teams:
        gf, ga = team_rolling_goal_avgs(historical, t)
        team_lam_mu[t] = simple_poisson_baseline(gf, ga, gf, ga, league_avg_goals)

    print(f"{cfg.display_name}: {len(remaining_fixtures)} real remaining league-phase fixtures, {N_TRIALS} trials")

    rng = np.random.default_rng(RNG_SEED)
    stage_order = ["eliminated_league_phase", "round_of_16", "quarter_final", "semi_final", "final", "winner"]
    reach_counts = {t: {s: 0 for s in stage_order} for t in teams}
    direct_r16_counts = {t: 0 for t in teams}
    playoff_zone_counts = {t: 0 for t in teams}

    for trial in range(N_TRIALS):
        points = dict(base_points)
        gf = dict(base_gf)
        ga = dict(base_ga)
        for home, away in remaining_fixtures:
            r_home, r_away = ratings.get(home, 1500.0), ratings.get(away, 1500.0)
            lam, mu = team_lam_mu[home][0], team_lam_mu[away][1]
            _, hg, ag = draw_match(rng, r_home, r_away, lam, mu)
            gf[home] += hg; ga[home] += ag
            gf[away] += ag; ga[away] += hg
            if hg > ag:
                points[home] += 3
            elif hg < ag:
                points[away] += 3
            else:
                points[home] += 1; points[away] += 1

        gd = {t: gf[t] - ga[t] for t in teams}
        ranking = sorted(teams, key=lambda t: (-points[t], -gd[t], -gf[t], t))

        top8 = ranking[:8]
        playoff_zone = ranking[8:24]
        for t in top8:
            direct_r16_counts[t] += 1
        for t in playoff_zone:
            playoff_zone_counts[t] += 1
        for t in ranking[24:]:
            reach_counts[t]["eliminated_league_phase"] += 1

        # Playoff round: ranks 9-16 seeded vs 17-24 unseeded (real UEFA
        # seeding rule, confirmed directly).
        seeded, unseeded = ranking[8:16], ranking[16:24]
        playoff_winners = draw_knockout_round(rng, seeded, unseeded, ratings, team_lam_mu)

        # Round of 16: top 8 seeded vs the 8 playoff winners unseeded.
        r16_field = top8 + playoff_winners
        for t in r16_field:
            reach_counts[t]["round_of_16"] += 1
        r16_winners = draw_knockout_round(rng, top8, playoff_winners, ratings, team_lam_mu)

        for t in r16_winners:
            reach_counts[t]["quarter_final"] += 1
        qf_winners = draw_open_round(rng, r16_winners, ratings, team_lam_mu)

        for t in qf_winners:
            reach_counts[t]["semi_final"] += 1
        sf_winners = draw_open_round(rng, qf_winners, ratings, team_lam_mu)

        for t in sf_winners:
            reach_counts[t]["final"] += 1
        finalist_a, finalist_b = sf_winners[0], sf_winners[1]
        # Final: single match, neutral venue -- no home advantage either side.
        lam_a, _ = team_lam_mu[finalist_a]
        _, mu_b = team_lam_mu[finalist_b]
        home_win, draw_p, away_win = elo_only_probabilities(ratings.get(finalist_a, 1500.0), ratings.get(finalist_b, 1500.0), home_advantage=0.0)
        result = rng.choice(["home_win", "draw", "away_win"], p=[home_win, draw_p, away_win])
        if result == "draw":
            winner = finalist_a if rng.random() < 0.5 else finalist_b
        else:
            winner = finalist_a if result == "home_win" else finalist_b
        reach_counts[winner]["winner"] += 1

    rows = []
    for t in teams:
        rows.append({
            "team": t,
            "current_elo": round(ratings.get(t, 1500.0), 1),
            "current_points": base_points[t], "current_goal_diff": base_gf[t] - base_ga[t],
            "prob_direct_round_of_16": round(direct_r16_counts[t] / N_TRIALS, 4),
            "prob_playoff_round_zone": round(playoff_zone_counts[t] / N_TRIALS, 4),
            "prob_eliminated_league_phase": round(reach_counts[t]["eliminated_league_phase"] / N_TRIALS, 4),
            "prob_reach_round_of_16": round(reach_counts[t]["round_of_16"] / N_TRIALS, 4),
            "prob_reach_quarter_final": round(reach_counts[t]["quarter_final"] / N_TRIALS, 4),
            "prob_reach_semi_final": round(reach_counts[t]["semi_final"] / N_TRIALS, 4),
            "prob_reach_final": round(reach_counts[t]["final"] / N_TRIALS, 4),
            "prob_win_competition": round(reach_counts[t]["winner"] / N_TRIALS, 4),
        })

    out_df = pd.DataFrame(rows).sort_values("prob_win_competition", ascending=False).reset_index(drop=True)
    out_df.insert(0, "n_trials", N_TRIALS)
    out_df["generated_at"] = now_utc_iso()
    out_df["model_version"] = MODEL_VERSION
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} team knockout probabilities to {out_path}")
    print(out_df[["team", "prob_direct_round_of_16", "prob_reach_semi_final", "prob_win_competition"]].head(10).to_string(index=False))


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["ucl", "uel", "uecl"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
