"""Central per-competition registry (spec: multi-league expansion).

Every pipeline script that used to hardcode EPL now takes a `league_id`
and looks up its real identity (data-source codes, sport key, team
count, timezone) here instead. `epl`'s file paths are unchanged from
before this registry existed (see `league_path`) -- adding this
registry did not move or rename any already-live data.

Run: python -m src.leagues (prints the registry, for a quick sanity check)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
LEAGUES_CONFIG_PATH = REPO_ROOT / "config" / "leagues.yaml"


@dataclass(frozen=True)
class LeagueConfig:
    league_id: str
    display_name: str
    country: str
    fixturedownload_slug: str
    odds_api_sport_key: str
    timezone: str
    n_teams: int
    match_id_prefix: str
    season: str = "2026-27"
    # "single_table" (default): a single round-robin table a team's own
    # season position/promotion/relegation makes sense for -- everything
    # this registry originally modeled. "groups": several small
    # round-robin groups with no combined table (e.g. UEFA Nations
    # League) -- table/races/season-simulation dashboard building does
    # not apply and must not run for these; see
    # single_table_league_ids() below.
    format: str = "single_table"
    # None for a competition football-data.co.uk genuinely has no real
    # coverage for (e.g. international competitions) -- collect_
    # historical_results.py and the spread/totals historical-odds
    # backtest are hard-coupled to this source and simply do not run
    # for such a league; a bespoke collector supplies its real
    # historical data instead. Never a placeholder/guessed code.
    football_data_code: str | None = None
    # None (default): simulate_full_season.py uses config/
    # simulation_config.yaml's global relegation_zone_size for this
    # league, correct for every European domestic league here so far.
    # 0 for a real competition with no relegation at all (e.g. MLS) --
    # 0 zero-size teams is a real, true statement ("0% relegation
    # probability for every team" is factually correct, not a rounding
    # artifact), never omit relegation_race entirely and never reuse
    # the global default, which would fabricate relegation risk for a
    # competition that has none.
    relegation_zone_size: int | None = None
    # None (default): simulate_full_season.py's hardcoded top_4/top_5
    # cutoffs apply unchanged (Champions League qualification zones).
    # An override lets a non-European competition's real promotion/
    # playoff line reuse the SAME already-computed "top_half_probability"
    # field (config/simulation_config.yaml's top_half_size) under a
    # different real meaning -- e.g. MLS's real 16-of-30 playoff field.
    playoff_zone_size: int | None = None


def _load_registry() -> dict[str, LeagueConfig]:
    with open(LEAGUES_CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    return {entry["league_id"]: LeagueConfig(**entry) for entry in raw["leagues"]}


_REGISTRY = _load_registry()


def load_league_config(league_id: str) -> LeagueConfig:
    if league_id not in _REGISTRY:
        raise KeyError(
            f"Unknown league_id '{league_id}'. Known leagues: {sorted(_REGISTRY)}. "
            f"Add a new entry to {LEAGUES_CONFIG_PATH} rather than guessing one."
        )
    return _REGISTRY[league_id]


def all_league_ids() -> list[str]:
    return sorted(_REGISTRY)


def single_table_league_ids() -> list[str]:
    """The subset of all_league_ids() a single expected-table/season-
    simulation/title-race dashboard genuinely applies to -- excludes
    "groups"-format competitions (see LeagueConfig.format) that have no
    combined table. Use this, not all_league_ids(), for any loop that
    builds a table, race, or season-simulation output."""
    return [lid for lid in all_league_ids() if _REGISTRY[lid].format == "single_table"]


def league_path(league_id: str, suffix: str) -> str:
    """Filename fragment for a per-league dataset, e.g.
    league_path("la_liga", "2026_27_fixtures.csv") ->
    "la_liga_2026_27_fixtures.csv". `epl` deliberately produces exactly
    the same names the repo already had before this registry existed
    (e.g. "epl_2026_27_fixtures.csv") -- no renaming of live data."""
    return f"{league_id}_{suffix}"


if __name__ == "__main__":
    for lid in all_league_ids():
        print(load_league_config(lid))
