"""Canonical club name registry and alias resolver, per league.

Different real data sources (football-data.co.uk, fixturedownload.com,
Wikipedia, official club branding) use different short/long forms for
the same club (e.g. "Man Utd", "Man United", "Manchester United"). This
module gives every club a single canonical full name per league so
data from multiple sources can be joined reliably.

The alias lists below were built from the actual source files pulled
during data collection for each league (football-data.co.uk's
per-season CSV, and fixturedownload.com's 2026-27 fixture feed), not
guessed.
"""
from __future__ import annotations

CANONICAL_TEAMS: dict[str, dict[str, list[str]]] = {
    "epl": {
        "Arsenal": ["Arsenal"],
        "Aston Villa": ["Aston Villa"],
        "AFC Bournemouth": ["Bournemouth"],
        "Brentford": ["Brentford"],
        "Brighton & Hove Albion": ["Brighton", "Brighton and Hove Albion"],
        "Burnley": ["Burnley"],
        "Cardiff City": ["Cardiff"],
        "Chelsea": ["Chelsea"],
        "Coventry City": ["Coventry"],
        "Crystal Palace": ["Crystal Palace"],
        "Everton": ["Everton"],
        "Fulham": ["Fulham"],
        "Huddersfield Town": ["Huddersfield"],
        "Hull City": ["Hull"],
        "Ipswich Town": ["Ipswich"],
        "Leeds United": ["Leeds"],
        "Leicester City": ["Leicester"],
        "Liverpool": ["Liverpool"],
        "Luton Town": ["Luton"],
        "Manchester City": ["Man City"],
        "Manchester United": ["Man United", "Man Utd"],
        "Middlesbrough": ["Middlesbrough"],
        "Newcastle United": ["Newcastle"],
        "Norwich City": ["Norwich"],
        "Nottingham Forest": ["Nott'm Forest", "Nottm Forest"],
        "Queens Park Rangers": ["QPR"],
        "Sheffield United": ["Sheffield United"],
        "Southampton": ["Southampton"],
        "Stoke City": ["Stoke"],
        "Sunderland": ["Sunderland"],
        "Swansea City": ["Swansea"],
        "Tottenham Hotspur": ["Tottenham", "Spurs"],
        "Watford": ["Watford"],
        "West Bromwich Albion": ["West Brom"],
        "West Ham United": ["West Ham"],
        "Wolverhampton Wanderers": ["Wolves"],
    },
    # Built from football-data.co.uk's real SP1.csv (2014/15-2025/26,
    # every team that appeared) cross-referenced against
    # fixturedownload.com's real 2026-27 La Liga fixture feed (the 20
    # actual 2026-27 clubs, including the 3 real promoted sides --
    # Racing Santander, Deportivo La Coruña, Málaga -- independently
    # confirmed via a live news search, same cross-check discipline
    # collect_fixtures.py already applies for EPL).
    "la_liga": {
        "Athletic Club": ["Ath Bilbao", "Athletic Bilbao"],
        "Atlético de Madrid": ["Ath Madrid", "Atletico Madrid"],
        "CA Osasuna": ["Osasuna"],
        "Celta Vigo": ["Celta"],
        "Deportivo Alavés": ["Alaves"],
        "Elche CF": ["Elche"],
        "FC Barcelona": ["Barcelona"],
        "Getafe CF": ["Getafe"],
        "Levante UD": ["Levante"],
        "Málaga CF": ["Malaga"],
        # "Santander" is the real name football-data.co.uk's live current-
        # season file uses (confirmed directly, 2026-09-16) -- absent from
        # the 2014/15-2025/26 historical window since Racing Santander's
        # last top-flight season predates it (14-year absence), so no
        # historical-season alias exists, only this live-feed one.
        "R. Racing Club": ["Santander"],
        "RC Deportivo": ["La Coruna"],
        "RCD Espanyol de Barcelona": ["Espanol"],
        "Rayo Vallecano": ["Vallecano"],
        "Real Betis": ["Betis"],
        "Real Madrid": ["Real Madrid"],
        "Real Sociedad": ["Sociedad"],
        "Sevilla FC": ["Sevilla"],
        "Valencia CF": ["Valencia"],
        "Villarreal CF": ["Villarreal"],
        # Historical-only clubs (2014/15-2025/26 real fd.co.uk data, not
        # in the 2026-27 fixture list) -- kept so backtest data can
        # still be normalized even though they're not this season's clubs.
        "UD Almería": ["Almeria"],
        "Cádiz CF": ["Cadiz"],
        "Córdoba CF": ["Cordoba"],
        "SD Eibar": ["Eibar"],
        "Girona FC": ["Girona"],
        "Granada CF": ["Granada"],
        "SD Huesca": ["Huesca"],
        "UD Las Palmas": ["Las Palmas"],
        "CD Leganés": ["Leganes"],
        "RCD Mallorca": ["Mallorca"],
        "Real Oviedo": ["Oviedo"],
        "Sporting Gijón": ["Sp Gijon"],
        "Real Valladolid": ["Valladolid"],
    },
}

_ALIAS_TO_CANONICAL: dict[str, dict[str, str]] = {}
for _league_id, _teams in CANONICAL_TEAMS.items():
    _table: dict[str, str] = {}
    for _canonical, _aliases in _teams.items():
        _table[_canonical.lower()] = _canonical
        for _alias in _aliases:
            _table[_alias.lower()] = _canonical
    _ALIAS_TO_CANONICAL[_league_id] = _table

EPL_2026_27_CLUBS: list[str] = sorted([
    "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford",
    "Brighton & Hove Albion", "Chelsea", "Coventry City", "Crystal Palace",
    "Everton", "Fulham", "Hull City", "Ipswich Town", "Leeds United",
    "Liverpool", "Manchester City", "Manchester United", "Newcastle United",
    "Nottingham Forest", "Sunderland", "Tottenham Hotspur",
])


def normalize_team_name(raw_name: str, league_id: str = "epl") -> str:
    """Map any known source variant of a club name to its canonical full
    name, within the given league's own alias table.

    Raises KeyError for unrecognized names rather than silently
    guessing, per the project's no-fabrication data rules.
    """
    if league_id not in _ALIAS_TO_CANONICAL:
        raise KeyError(f"No canonical team table for league_id '{league_id}'.")
    key = raw_name.strip().lower()
    table = _ALIAS_TO_CANONICAL[league_id]
    if key not in table:
        raise KeyError(
            f"Unrecognized team name '{raw_name}' for league '{league_id}'. Add it to "
            "CANONICAL_TEAMS in src/utils/team_names.py rather than guessing a mapping."
        )
    return table[key]
