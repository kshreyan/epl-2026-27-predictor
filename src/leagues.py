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
    football_data_code: str
    fixturedownload_slug: str
    odds_api_sport_key: str
    timezone: str
    n_teams: int
    match_id_prefix: str
    season: str = "2026-27"


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
