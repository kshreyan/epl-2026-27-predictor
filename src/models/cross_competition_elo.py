"""Domestic-league Elo ratings as a cross-competition PRIOR SEED for the
UEFA club competitions (src/evaluation/backtest_continental_cup.py and
friends) -- the highest-value fix identified for their accuracy: each
competition's own real data (2 seasons, ~270-290 scored league-phase
matches total across 36 teams) is far too thin to estimate relative
strength well on its own. Confirmed directly during this project: RC
Lens, with only 2 real UCL matches, produced a near-certain (89% cover
probability) Dixon-Coles margin-survival verdict purely from sample-
size noise -- exactly the failure mode a better starting prior fixes.

Each of the 5 domestic leagues this project tracks (EPL, La Liga,
Serie A, Bundesliga, Ligue 1) has 2,000+ real historical matches and a
far more reliable Elo estimate for any of its own clubs. This module
computes each domestic league's current Elo ratings (same run_elo
engine, same hyperparameters, real historical + real completed-2026-27
results) and merges them into one team -> rating lookup, passed as
`seed_ratings` into a continental competition's own run_elo call (the
same mechanism the old, now-removed Nations League predictor used for
its real UEFA-tier seed) -- real continental results still move the
rating from there every real match played; only the STARTING point
changes.

**Real, honest limitation: partial coverage only.** A club playing in
a domestic league this project doesn't track (Portugal, Netherlands,
Belgium, Turkey, Scotland, Czechia, and dozens of others -- the
majority of smaller-league UEFA entrants) gets no domestic signal at
all and still starts from a flat 1500, same as before this module
existed. Run this module directly to print real coverage counts per
competition.

Run: python -m src.models.cross_competition_elo
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.models.elo_model import run_elo  # noqa: E402
from src.utils.team_names import CANONICAL_TEAMS  # noqa: E402

MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"
DOMESTIC_LEAGUE_IDS = ["epl", "la_liga", "serie_a", "bundesliga", "ligue_1"]

# Continental canonical name -> domestic canonical name, for the real
# cases confirmed directly where the two leagues' own CANONICAL_TEAMS
# entries (built independently, in different project phases) use
# genuinely different spellings with NO shared alias to bridge them
# automatically (e.g. Serie A's canonical "Roma" vs this project's own
# continental canonical "AS Roma" -- both real, neither wrong, just
# different). Alias-table expansion (see _domestic_elo_ratings) already
# resolves most cross-spelling cases (e.g. La Liga's "FC Barcelona" ->
# alias "Barcelona" already matches the continental name with no entry
# needed here) -- this dict is only the real leftover gap, not a
# duplicate of the alias mechanism.
MANUAL_NAME_OVERRIDES = {
    "AS Roma": "Roma",
    "Inter Milan": "Internazionale",
    "Atlético Madrid": "Atlético de Madrid",
    "AC Milan": "Milan",
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
}


def _domestic_elo_ratings(league_id: str, as_of_date: "pd.Timestamp | None" = None) -> dict[str, float]:
    """team name (canonical OR any registered alias for that league) ->
    domestic Elo rating. Alias expansion means a continental team name
    that happens to match one of THIS league's own real alias spellings
    (not just its canonical form) still finds the real rating.

    `as_of_date`, when given, drops every real domestic match on or
    after it before fitting -- REQUIRED for leak-free use inside
    backtest_continental_cup.py's walk-forward loop (seeding a 2024-25
    continental-match prediction with 2026-27 domestic form would be
    real data leakage, not a fair backtest). Omit it only for a live
    prediction, where every currently-available real result is fair
    game."""
    with open(MODEL_CONFIG_PATH) as f:
        elo_cfg = yaml.safe_load(f)["elo"]

    hist_path = REPO_ROOT / "data" / "raw" / f"{league_id}_historical_matches.csv"
    completed_path = REPO_ROOT / "data" / "raw" / f"{league_id}_2026_27_completed_matches.csv"

    df = pd.read_csv(hist_path, parse_dates=["date"])
    if completed_path.exists():
        completed = pd.read_csv(completed_path, parse_dates=["date"])
        if not completed.empty:
            df = pd.concat([df, completed], ignore_index=True)
    df = df.dropna(subset=["home_goals", "away_goals"])
    if as_of_date is not None:
        df = df[df["date"] < as_of_date]
    if df.empty:
        return {}

    elo_run = run_elo(df, k_factor=elo_cfg["k_factor"], home_advantage=elo_cfg["home_advantage_elo_points"])
    by_canonical = dict(elo_run.final_ratings)

    expanded: dict[str, float] = {}
    for canonical, rating in by_canonical.items():
        expanded[canonical] = rating
    for canonical, aliases in CANONICAL_TEAMS.get(league_id, {}).items():
        if canonical not in by_canonical:
            continue
        for alias in aliases:
            expanded[alias] = by_canonical[canonical]
    return expanded


def cross_competition_seed_ratings(as_of_date: "pd.Timestamp | None" = None) -> dict[str, float]:
    """Continental team name -> domestic Elo, merged across all 5
    covered leagues (alias-expanded) plus the small real manual-override
    bridge (MANUAL_NAME_OVERRIDES) for the genuine cross-league spelling
    gaps alias expansion alone doesn't close. A team name that appears
    in more than one league's own ratings (should not happen for a real
    club, but guarded rather than assumed) keeps whichever league is
    processed last in DOMESTIC_LEAGUE_IDS -- logged to stdout if it
    ever actually occurs, never silently resolved.

    `as_of_date`: see _domestic_elo_ratings -- pass this inside any
    walk-forward/backtest loop; omit only for a live, present-day seed."""
    merged: dict[str, float] = {}
    seen_in: dict[str, str] = {}
    for league_id in DOMESTIC_LEAGUE_IDS:
        ratings = _domestic_elo_ratings(league_id, as_of_date=as_of_date)
        for team, rating in ratings.items():
            if team in seen_in and seen_in[team] != league_id:
                print(f"WARNING: '{team}' has domestic Elo in both {seen_in[team]} and {league_id} -- "
                      f"using {league_id}'s value. Investigate a possible real team-name collision.")
            merged[team] = rating
            seen_in[team] = league_id

    for continental_name, domestic_name in MANUAL_NAME_OVERRIDES.items():
        if continental_name not in merged and domestic_name in merged:
            merged[continental_name] = merged[domestic_name]
    return merged


def should_use_domestic_seed(league_id: str) -> bool:
    """Whether THIS competition's own real backtest
    (backtest_continental_cup.py) found the domestic-Elo-seeded Elo
    variant beats the flat-start one -- it did for UCL (21/36 teams
    covered), not for UEL or UECL (12/36, 4/36). Never assumed; always
    read from the real comparison CSV that backtest wrote. Defaults to
    False (flat start, the safe/previously-validated choice) if that
    backtest hasn't been run yet for this league."""
    comparison_path = REPO_ROOT / "data" / "outputs" / f"{league_id}_backtest_model_comparison.csv"
    if not comparison_path.exists():
        return False
    comparison = pd.read_csv(comparison_path).sort_values("log_loss")
    return bool(comparison.iloc[0]["model"] == "Elo-only, domestic-Elo-seeded")


def main() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from src.leagues import load_league_config  # noqa: E402

    seeds = cross_competition_seed_ratings()
    print(f"Computed real domestic Elo for {len(seeds)} clubs across {len(DOMESTIC_LEAGUE_IDS)} leagues.\n")

    for league_id in ["ucl", "uel", "uecl"]:
        fixtures_path = REPO_ROOT / "data" / "raw" / f"{league_id}_2026_27_fixtures.csv"
        if not fixtures_path.exists():
            continue
        cfg = load_league_config(league_id)
        fixtures = pd.read_csv(fixtures_path)
        teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
        covered = [t for t in teams if t in seeds]
        print(f"{cfg.display_name}: {len(covered)}/{len(teams)} teams get a real domestic-Elo seed")
        print(f"  covered: {covered}")
        print(f"  no domestic signal (flat 1500 start): {[t for t in teams if t not in seeds]}\n")


if __name__ == "__main__":
    main()
