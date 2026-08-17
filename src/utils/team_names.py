"""Canonical Premier League club name registry and alias resolver.

Different real data sources (football-data.co.uk, fixturedownload.com,
Wikipedia, official Premier League branding) use different short/long
forms for the same club (e.g. "Man Utd", "Man United", "Manchester
United"). This module gives every club a single canonical full name so
data from multiple sources can be joined reliably.

The alias lists below were built from the actual source files pulled
during data collection (football-data.co.uk E0.csv, 2014/15-2025/26,
and fixturedownload.com's 2026-27 EPL fixture feed), not guessed.
"""
from __future__ import annotations

CANONICAL_TEAMS: dict[str, list[str]] = {
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
}

_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in CANONICAL_TEAMS.items():
    _ALIAS_TO_CANONICAL[_canonical.lower()] = _canonical
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canonical

EPL_2026_27_CLUBS: list[str] = sorted([
    "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford",
    "Brighton & Hove Albion", "Chelsea", "Coventry City", "Crystal Palace",
    "Everton", "Fulham", "Hull City", "Ipswich Town", "Leeds United",
    "Liverpool", "Manchester City", "Manchester United", "Newcastle United",
    "Nottingham Forest", "Sunderland", "Tottenham Hotspur",
])


def normalize_team_name(raw_name: str) -> str:
    """Map any known source variant of a club name to its canonical full name.

    Raises KeyError for unrecognized names rather than silently guessing,
    per the project's no-fabrication data rules.
    """
    key = raw_name.strip().lower()
    if key not in _ALIAS_TO_CANONICAL:
        raise KeyError(
            f"Unrecognized team name '{raw_name}'. Add it to "
            "CANONICAL_TEAMS in src/utils/team_names.py rather than "
            "guessing a mapping."
        )
    return _ALIAS_TO_CANONICAL[key]
