"""Monte Carlo simulation of the rest of the real NFL/NBA regular
season, producing the real playoff picture: make-playoffs probability,
win-division probability, and a real seed distribution per team. NCAA
Football gets a genuinely different real target instead (see below).

**Scope boundary: this simulates who makes the playoffs and as what
seed, not the playoff bracket itself** (no simulated Super Bowl/NBA
champion) -- a distinct follow-on, same as how the soccer knockout
bracket was a separate ask after the base UCL/UEL/UECL build.

Real NFL/NBA divisions/conferences are hardcoded below (stable public
facts, unchanged in years -- same discipline as hardcoding a real club
roster in team_names.py, not derived from a fragile API ID chain --
ESPN's own team-group IDs resolve to division/conference names only
through a separate, undocumented lookup, confirmed directly not worth
the fragility for a fact this stable). **NCAA Football's real
conference groupings are NOT hardcoded** -- fetched live from ESPN at
run time (espn_api.fetch_real_fbs_conferences()), since real
conference realignment is a recurring event in college sports, unlike
these two sports' stable structure.

Real seeding rules (confirmed directly via research, not assumed):
- **NFL**: 7 seeds per conference -- the 4 division winners (seeded
  1-4 by real record), then the next 3 best remaining records as
  wildcards (seeded 5-7). Only the #1 seed gets a real first-round bye.
- **NBA**: top 6 per conference qualify directly (seeds 1-6); 7th-10th
  enter the real play-in tournament for the final 2 playoff spots
  (reported here as a single "play-in zone" probability, since
  simulating the actual play-in games is outside this build's scope);
  11th and below are eliminated.
- **NCAA Football has no real seeding formula to simulate** -- the
  real 12-team College Football Playoff is committee-selected, not a
  standings formula, and this project will not fabricate a substitute
  for human judgment (see config/leagues.yaml's NCAA Football note).
  Instead this module reports a real, honestly-computable target for
  this sport: each team's real conference win-loss projection and
  `prob_bowl_eligible` = P(finish the season with 6 or more real wins,
  the real NCAA bowl-eligibility rule).

Every simulated game (including NBA/NCAA Football, where the Elo-only
model separately won each league's own real moneyline backtest -- see
predict_team_sport_matches.py) is drawn from the
point-margin model's own Normal(mean, sigma) distribution, not
whichever model won that league's moneyline backtest: simulating a
real, tiebreaker-relevant point differential needs a real margin
model, and Elo-only has no margin concept at all -- same reasoning
compute_margin_survival_team_sport.py already uses.

Real tiebreakers used: win percentage (a tie counts as half a win),
then real point differential, then a fixed deterministic fallback
(alphabetical team name) -- NOT the full official multi-step real
tiebreaker procedure (head-to-head, common games, strength of victory/
schedule, conference record, etc.), same simplification
simulate_full_season.py already makes for EPL ("head-to-head is NOT
implemented... broken by a fixed, documented, deterministic rule").

Ratings are held fixed at today's value for every simulated trial --
same real limitation simulate_continental_cup_knockout.py already
discloses (does not propagate rating uncertainty the way the domestic
Dixon-Coles season simulator does).

Run: python -m src.simulation.simulate_team_sport_season --league nfl
(also accepts nba, ncaaf)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection.espn_api import fetch_real_fbs_conferences  # noqa: E402
from src.evaluation.backtest_team_sport import ALLOWS_TIES, ELO_K_FACTOR  # noqa: E402
from src.leagues import league_path, load_league_config  # noqa: E402
from src.models.point_margin_model import fit_point_margin_model, predict_margin_distribution  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

BOWL_ELIGIBLE_WINS = 6  # real NCAA rule: 6+ real wins in a real season makes a team bowl-eligible

N_TRIALS = 10000
RNG_SEED = 20261021  # fixed seed -- reproducible trial-to-trial, not re-randomized on every re-run

CONFERENCES = {
    "nfl": {
        "AFC": {
            "AFC East": ["Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets"],
            "AFC North": ["Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers"],
            "AFC South": ["Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans"],
            "AFC West": ["Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers"],
        },
        "NFC": {
            "NFC East": ["Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders"],
            "NFC North": ["Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings"],
            "NFC South": ["Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers"],
            "NFC West": ["Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"],
        },
    },
    "nba": {
        "Eastern": {
            "Atlantic": ["Boston Celtics", "Brooklyn Nets", "New York Knicks", "Philadelphia 76ers", "Toronto Raptors"],
            "Central": ["Chicago Bulls", "Cleveland Cavaliers", "Detroit Pistons", "Indiana Pacers", "Milwaukee Bucks"],
            "Southeast": ["Atlanta Hawks", "Charlotte Hornets", "Miami Heat", "Orlando Magic", "Washington Wizards"],
        },
        "Western": {
            "Northwest": ["Denver Nuggets", "Minnesota Timberwolves", "Oklahoma City Thunder", "Portland Trail Blazers", "Utah Jazz"],
            "Pacific": ["Golden State Warriors", "LA Clippers", "Los Angeles Lakers", "Phoenix Suns", "Sacramento Kings"],
            "Southwest": ["Dallas Mavericks", "Houston Rockets", "Memphis Grizzlies", "New Orleans Pelicans", "San Antonio Spurs"],
        },
    },
}

DIRECT_SEEDS = {"nfl": 4, "nba": 6}  # NFL: 4 division winners seeded 1-4; NBA: top 6 seeded 1-6
TOTAL_SEEDS = {"nfl": 7, "nba": 8}  # NFL: 7 total (4 division + 3 wildcard); NBA: 8 after the real play-in


def team_division_conference(league_id: str) -> tuple[dict[str, str], dict[str, str]]:
    team_division, team_conference = {}, {}
    for conf, divisions in CONFERENCES[league_id].items():
        for div, teams in divisions.items():
            for t in teams:
                team_division[t] = div
                team_conference[t] = conf
    return team_division, team_conference


def rank_conference(teams: list[str], win_pct: dict[str, float], point_diff: dict[str, float]) -> list[str]:
    return sorted(teams, key=lambda t: (-win_pct[t], -point_diff[t], t))


def nfl_seeding(conf_teams: list[str], team_division: dict[str, str], win_pct: dict[str, float], point_diff: dict[str, float]) -> list[str]:
    """Real NFL rule: the best-record team in each of the conference's 4
    real divisions is a division winner (seeded 1-4 by record among
    themselves); the next-best 3 remaining records are wildcards
    (seeded 5-7)."""
    divisions_in_conf = sorted(set(team_division[t] for t in conf_teams))
    division_winners = []
    for div in divisions_in_conf:
        div_teams = [t for t in conf_teams if team_division[t] == div]
        division_winners.append(rank_conference(div_teams, win_pct, point_diff)[0])
    division_winners_ranked = rank_conference(division_winners, win_pct, point_diff)

    remaining = [t for t in conf_teams if t not in division_winners]
    wildcards_ranked = rank_conference(remaining, win_pct, point_diff)[:3]
    return division_winners_ranked + wildcards_ranked


def main_seeded_playoff(league_id: str) -> None:
    cfg = load_league_config(league_id)
    allows_ties = ALLOWS_TIES[league_id]
    historical_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path(league_id, "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path(league_id, "2026_27_playoff_picture.csv")

    team_division, team_conference = team_division_conference(league_id)

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures = pd.read_csv(fixtures_path)
    real_results = pd.read_csv(real_results_path) if real_results_path.exists() else pd.DataFrame(columns=["match_id", "home_goals", "away_goals"])
    results_by_id = real_results.set_index("match_id") if not real_results.empty else real_results

    teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    assert set(teams) <= set(team_division), f"{league_id}: real fixture teams not all in the hardcoded division structure: {set(teams) - set(team_division)}"

    base_wins = {t: 0.0 for t in teams}
    base_games = {t: 0 for t in teams}
    base_point_diff = {t: 0 for t in teams}
    remaining_fixtures = []
    completed_rows = []
    for _, fx in fixtures.iterrows():
        if fx["match_id"] in results_by_id.index:
            rr = results_by_id.loc[fx["match_id"]]
            hg, ag = int(rr["home_goals"]), int(rr["away_goals"])
            home, away = fx["home_team"], fx["away_team"]
            base_games[home] += 1; base_games[away] += 1
            base_point_diff[home] += hg - ag; base_point_diff[away] += ag - hg
            if hg > ag:
                base_wins[home] += 1
            elif hg < ag:
                base_wins[away] += 1
            else:
                base_wins[home] += 0.5; base_wins[away] += 0.5
            completed_rows.append({"date": pd.Timestamp(fx["date"]), "home_team": home, "away_team": away, "home_score": hg, "away_score": ag})
        else:
            remaining_fixtures.append((fx["home_team"], fx["away_team"]))

    if completed_rows:
        historical = pd.concat([historical, pd.DataFrame(completed_rows)], ignore_index=True)

    fit = fit_point_margin_model(historical, allows_ties=allows_ties, k_factor=ELO_K_FACTOR)
    print(f"{cfg.display_name}: {len(remaining_fixtures)} real remaining games, {N_TRIALS} trials")

    rng = np.random.default_rng(RNG_SEED)
    direct_count = {t: 0 for t in teams}
    playoff_zone_count = {t: 0 for t in teams}  # all TOTAL_SEEDS seeds, direct + wildcard/play-in
    division_winner_count = {t: 0 for t in teams}
    seed_counts = {t: {s: 0 for s in range(1, TOTAL_SEEDS[league_id] + 1)} for t in teams}

    for _ in range(N_TRIALS):
        games_played = dict(base_games)
        wins = dict(base_wins)
        point_diff = dict(base_point_diff)

        for home, away in remaining_fixtures:
            mean, sigma = predict_margin_distribution(fit, home, away)
            margin = rng.normal(mean, sigma)
            margin_int = round(margin)
            if allows_ties and margin_int == 0:
                wins[home] += 0.5; wins[away] += 0.5
            elif margin_int > 0:
                wins[home] += 1
            else:
                wins[away] += 1
            point_diff[home] += margin_int; point_diff[away] -= margin_int
            games_played[home] += 1; games_played[away] += 1

        win_pct = {t: wins[t] / games_played[t] if games_played[t] else 0.0 for t in teams}

        for conf, divisions in CONFERENCES[league_id].items():
            conf_teams = [t for div_teams in divisions.values() for t in div_teams]
            if league_id == "nfl":
                ranked = nfl_seeding(conf_teams, team_division, win_pct, point_diff)
                for div in divisions:
                    div_teams = [t for t in conf_teams if team_division[t] == div]
                    division_winner_count[rank_conference(div_teams, win_pct, point_diff)[0]] += 1
            else:
                ranked = rank_conference(conf_teams, win_pct, point_diff)

            for seed, team in enumerate(ranked[:TOTAL_SEEDS[league_id]], start=1):
                seed_counts[team][seed] += 1
                playoff_zone_count[team] += 1
                if seed <= DIRECT_SEEDS[league_id]:
                    direct_count[team] += 1

    rows = []
    for t in teams:
        row = {
            "team": t, "conference": team_conference[t], "division": team_division[t],
            "current_win_pct": round(base_wins[t] / base_games[t], 4) if base_games[t] else None,
            "current_point_diff": base_point_diff[t],
            "prob_make_playoffs": round(playoff_zone_count[t] / N_TRIALS, 4),
            "prob_direct_seed": round(direct_count[t] / N_TRIALS, 4),
        }
        if league_id == "nfl":
            row["prob_win_division"] = round(division_winner_count[t] / N_TRIALS, 4)
        for seed in range(1, TOTAL_SEEDS[league_id] + 1):
            row[f"prob_seed_{seed}"] = round(seed_counts[t][seed] / N_TRIALS, 4)
        rows.append(row)

    out_df = pd.DataFrame(rows).sort_values(["conference", "prob_make_playoffs"], ascending=[True, False]).reset_index(drop=True)
    out_df.insert(0, "n_trials", N_TRIALS)
    out_df["generated_at"] = now_utc_iso()
    out_df["model_version"] = MODEL_VERSION
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} team playoff-picture rows to {out_path}")


def main_ncaaf_bowl_eligibility() -> None:
    """NCAA Football's own real target -- see module docstring for why
    this is NOT a seeded-playoff simulation: real conference win-loss
    projection (conference games only, the real basis for actual
    conference standings) and `prob_bowl_eligible` = P(finish the real
    season with BOWL_ELIGIBLE_WINS (6) or more real total wins)."""
    cfg = load_league_config("ncaaf")
    allows_ties = ALLOWS_TIES["ncaaf"]
    historical_path = REPO_ROOT / "data" / "raw" / league_path("ncaaf", "historical_matches.csv")
    fixtures_path = REPO_ROOT / "data" / "raw" / league_path("ncaaf", "2026_27_fixtures.csv")
    real_results_path = REPO_ROOT / "data" / "raw" / league_path("ncaaf", "2026_27_real_results.csv")
    out_path = REPO_ROOT / "data" / "outputs" / league_path("ncaaf", "2026_27_playoff_picture.csv")

    conferences = fetch_real_fbs_conferences()
    team_conference = {t["display_name"]: conf for conf, roster in conferences.items() for t in roster}

    historical = pd.read_csv(historical_path, parse_dates=["date"])
    fixtures = pd.read_csv(fixtures_path)
    real_results = pd.read_csv(real_results_path) if real_results_path.exists() else pd.DataFrame(columns=["match_id", "home_goals", "away_goals"])
    results_by_id = real_results.set_index("match_id") if not real_results.empty else real_results

    teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    # A handful of real teams can be mid-transition between divisions
    # (e.g. a real independent not yet assigned a real conference this
    # season) -- grouped under a real "Unaffiliated" bucket rather than
    # dropped, so every real team with real fixtures still gets a row.
    for t in teams:
        team_conference.setdefault(t, "Unaffiliated")

    base_wins = {t: 0.0 for t in teams}
    base_games = {t: 0 for t in teams}
    base_conf_wins = {t: 0.0 for t in teams}
    base_conf_games = {t: 0 for t in teams}
    remaining_fixtures = []
    completed_rows = []
    for _, fx in fixtures.iterrows():
        home, away = fx["home_team"], fx["away_team"]
        same_conf = team_conference.get(home) == team_conference.get(away)
        if fx["match_id"] in results_by_id.index:
            rr = results_by_id.loc[fx["match_id"]]
            hg, ag = int(rr["home_goals"]), int(rr["away_goals"])
            base_games[home] += 1; base_games[away] += 1
            if same_conf:
                base_conf_games[home] += 1; base_conf_games[away] += 1
            if hg > ag:
                base_wins[home] += 1
                if same_conf:
                    base_conf_wins[home] += 1
            elif hg < ag:
                base_wins[away] += 1
                if same_conf:
                    base_conf_wins[away] += 1
            else:
                base_wins[home] += 0.5; base_wins[away] += 0.5
                if same_conf:
                    base_conf_wins[home] += 0.5; base_conf_wins[away] += 0.5
            completed_rows.append({"date": pd.Timestamp(fx["date"]), "home_team": home, "away_team": away, "home_score": hg, "away_score": ag})
        else:
            remaining_fixtures.append((home, away, same_conf))

    if completed_rows:
        historical = pd.concat([historical, pd.DataFrame(completed_rows)], ignore_index=True)

    # Real conference-aware reversion -- confirmed via a real paired-
    # bootstrap test to beat flat reversion for this league's own real
    # margin task (see predict_team_sport_matches.py's identical wiring
    # and reports/ncaaf_model_selection_report.md). Reuses this
    # function's own already-fetched `team_conference` above rather
    # than a second real API call.
    fit = fit_point_margin_model(historical, allows_ties=allows_ties, k_factor=ELO_K_FACTOR, team_group=team_conference)
    print(f"{cfg.display_name}: {len(remaining_fixtures)} real remaining games, {N_TRIALS} trials")

    rng = np.random.default_rng(RNG_SEED)
    bowl_eligible_count = {t: 0 for t in teams}
    total_wins_sum = {t: 0.0 for t in teams}
    conf_best_record_count = {t: 0 for t in teams}

    for _ in range(N_TRIALS):
        wins = dict(base_wins)
        conf_wins = dict(base_conf_wins)
        conf_games = dict(base_conf_games)

        for home, away, same_conf in remaining_fixtures:
            mean, sigma = predict_margin_distribution(fit, home, away)
            margin = rng.normal(mean, sigma)
            margin_int = round(margin)
            if margin_int > 0:
                wins[home] += 1
                if same_conf:
                    conf_wins[home] += 1
            else:
                wins[away] += 1
                if same_conf:
                    conf_wins[away] += 1
            if same_conf:
                conf_games[home] += 1; conf_games[away] += 1

        for t in teams:
            total_wins_sum[t] += wins[t]
            if wins[t] >= BOWL_ELIGIBLE_WINS:
                bowl_eligible_count[t] += 1

        for conf in conferences:
            conf_teams = [t for t in teams if team_conference.get(t) == conf]
            if not conf_teams:
                continue
            conf_win_pct = {t: (conf_wins[t] / conf_games[t] if conf_games[t] else 0.0) for t in conf_teams}
            best = max(conf_teams, key=lambda t: (conf_win_pct[t], t))
            conf_best_record_count[best] += 1

    rows = []
    for t in teams:
        rows.append({
            "team": t, "conference": team_conference.get(t, "Unaffiliated"),
            "current_wins": base_wins[t], "current_games": base_games[t],
            "current_conference_win_pct": round(base_conf_wins[t] / base_conf_games[t], 4) if base_conf_games[t] else None,
            "mean_projected_final_wins": round(total_wins_sum[t] / N_TRIALS, 2),
            "prob_bowl_eligible": round(bowl_eligible_count[t] / N_TRIALS, 4),
            "prob_best_conference_record": round(conf_best_record_count[t] / N_TRIALS, 4),
        })

    out_df = pd.DataFrame(rows).sort_values(["conference", "prob_bowl_eligible"], ascending=[True, False]).reset_index(drop=True)
    out_df.insert(0, "n_trials", N_TRIALS)
    out_df["generated_at"] = now_utc_iso()
    out_df["model_version"] = MODEL_VERSION
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} team bowl-eligibility rows to {out_path}")


def main(league_id: str) -> None:
    if league_id == "ncaaf":
        main_ncaaf_bowl_eligibility()
    else:
        main_seeded_playoff(league_id)


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--league", required=True, choices=["nfl", "nba", "ncaaf"], dest="league_id")
    _args = _parser.parse_args()
    main(league_id=_args.league_id)
