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
    # Built from football-data.co.uk's real I1.csv (2014/15-2025/26, every
    # team that appeared across all 12 seasons) cross-referenced against
    # fixturedownload.com's real 2026-27 Serie A fixture feed (the 20
    # actual 2026-27 clubs). Only one club's name actually differs between
    # the two real sources -- football-data.co.uk's live/historical files
    # say "Inter", fixturedownload.com's 2026-27 feed says "Internazionale"
    # -- every other club's short name already matches across both sources
    # (Italian clubs' common short names, e.g. "Milan" not "AC Milan",
    # "Roma" not "AS Roma", are what both real sources already use, so
    # nothing was invented here). The 3 real 2026-27 promoted clubs
    # (Frosinone, Monza, Venezia) fall out automatically from
    # derive_promoted_teams() -- all three already appear in the 12-season
    # historical window (previously relegated, now back up), so no
    # separate promoted-club verification was needed the way La Liga's was.
    "serie_a": {
        "Atalanta": ["Atalanta"],
        "Bologna": ["Bologna"],
        "Cagliari": ["Cagliari"],
        "Como": ["Como"],
        "Fiorentina": ["Fiorentina"],
        "Frosinone": ["Frosinone"],
        "Genoa": ["Genoa"],
        "Internazionale": ["Inter"],
        "Juventus": ["Juventus"],
        "Lazio": ["Lazio"],
        "Lecce": ["Lecce"],
        "Milan": ["Milan"],
        "Monza": ["Monza"],
        "Napoli": ["Napoli"],
        "Parma": ["Parma"],
        "Roma": ["Roma"],
        "Sassuolo": ["Sassuolo"],
        "Torino": ["Torino"],
        "Udinese": ["Udinese"],
        "Venezia": ["Venezia"],
        # Historical-only clubs (2014/15-2025/26 real fd.co.uk data, not in
        # the 2026-27 fixture list) -- kept so backtest data can still be
        # normalized even though they're not this season's clubs.
        "Benevento": ["Benevento"],
        "Brescia": ["Brescia"],
        "Carpi": ["Carpi"],
        "Cesena": ["Cesena"],
        "Chievo": ["Chievo"],
        "Cremonese": ["Cremonese"],
        "Crotone": ["Crotone"],
        "Empoli": ["Empoli"],
        "Palermo": ["Palermo"],
        "Pescara": ["Pescara"],
        "Pisa": ["Pisa"],
        "Salernitana": ["Salernitana"],
        "Sampdoria": ["Sampdoria"],
        "Spal": ["Spal"],
        "Spezia": ["Spezia"],
        "Verona": ["Verona"],
    },
    # Built from football-data.co.uk's real D1.csv (2014/15-2025/26, every
    # team that appeared across all 12 seasons, plus the live 2026-27
    # current-season file) cross-referenced against fixturedownload.com's
    # real 2026-27 Bundesliga fixture feed (the 18 actual 2026-27 clubs --
    # Bundesliga has 18 teams, not 20 like EPL/La Liga/Serie A). Every
    # short name below is exactly what football-data.co.uk's own files
    # use; nothing invented. One 2026-27 promoted club, SV Elversberg, has
    # no alias in the 2014/15-2025/26 historical window (this is its
    # first-ever top-flight season in that span) -- its alias comes only
    # from the live 2026-27 file, the same situation La Liga's Racing
    # Santander case was in. The other two real 2026-27 promoted clubs,
    # FC Schalke 04 and SC Paderborn 07, both already appear in the
    # 12-season historical window (previously relegated, now back up).
    "bundesliga": {
        "1. FC Köln": ["FC Koln"],
        "1. FC Union Berlin": ["Union Berlin"],
        "1. FSV Mainz 05": ["Mainz"],
        "Bayer 04 Leverkusen": ["Leverkusen"],
        "Borussia Dortmund": ["Dortmund"],
        "Borussia Mönchengladbach": ["M'gladbach"],
        "Eintracht Frankfurt": ["Ein Frankfurt"],
        "FC Augsburg": ["Augsburg"],
        "FC Bayern München": ["Bayern Munich"],
        "FC Schalke 04": ["Schalke 04"],
        "Hamburger SV": ["Hamburg"],
        "RB Leipzig": ["RB Leipzig"],
        "SC Paderborn 07": ["Paderborn"],
        "SV Elversberg": ["Elversberg"],
        "SV Werder Bremen": ["Werder Bremen"],
        "Sport-Club Freiburg": ["Freiburg"],
        "TSG Hoffenheim": ["Hoffenheim"],
        "VfB Stuttgart": ["Stuttgart"],
        # Historical-only clubs (2014/15-2025/26 real fd.co.uk data, not in
        # the 2026-27 fixture list) -- kept so backtest data can still be
        # normalized even though they're not this season's clubs.
        "Bielefeld": ["Bielefeld"],
        "Bochum": ["Bochum"],
        "Darmstadt": ["Darmstadt"],
        "Fortuna Dusseldorf": ["Fortuna Dusseldorf"],
        "Greuther Furth": ["Greuther Furth"],
        "Hannover": ["Hannover"],
        "Heidenheim": ["Heidenheim"],
        "Hertha": ["Hertha"],
        "Holstein Kiel": ["Holstein Kiel"],
        "Ingolstadt": ["Ingolstadt"],
        "Nurnberg": ["Nurnberg"],
        "St Pauli": ["St Pauli"],
        "Wolfsburg": ["Wolfsburg"],
    },
    # Built from football-data.co.uk's real F1.csv (2014/15-2025/26, every
    # team that appeared across all 12 seasons -- Ligue 1 played 20 teams
    # through 2022/23 then dropped to 18 from 2023/24 on, plus a real
    # abandoned 2019/20 season (COVID) -- both reflected as-is, not
    # normalized away) cross-referenced against fixturedownload.com's real
    # 2026-27 Ligue 1 fixture feed (18 clubs) and, independently, the-odds-
    # api.com's live event list for the same season (used as the second
    # real source for cross-verification). One 2026-27 club, Le Mans FC,
    # has no alias in the 2014/15-2025/26 historical window (no top-flight
    # appearance in that span, confirmed absent from both the historical
    # file and corroborated by its presence in both real live sources) --
    # the same situation La Liga's Racing Santander and Bundesliga's SV
    # Elversberg cases were in. The other 2026-27 promoted club, Estac
    # Troyes, already appears in the 12-season historical window
    # (previously relegated, now back up). Paris Saint-Germain has two
    # real source spellings ("Paris SG" from football-data.co.uk, "Paris
    # Saint Germain" from the Odds API) -- both kept, nothing invented.
    "ligue_1": {
        "AJ Auxerre": ["Auxerre"],
        "AS Monaco": ["Monaco"],
        "Angers SCO": ["Angers"],
        "Estac Troyes": ["Troyes"],
        "FC Lorient": ["Lorient"],
        "Havre Athletic Club": ["Le Havre"],
        "LOSC Lille": ["Lille"],
        "Le Mans FC": ["Le Mans FC", "Le Mans"],
        "OGC Nice": ["Nice"],
        "Olympique Lyonnais": ["Lyon"],
        "Olympique de Marseille": ["Marseille"],
        "Paris FC": ["Paris FC"],
        "Paris Saint-Germain": ["Paris SG", "Paris Saint Germain"],
        "RC Lens": ["Lens"],
        "RC Strasbourg Alsace": ["Strasbourg"],
        "Stade Brestois 29": ["Brest"],
        "Stade Rennais FC": ["Rennes"],
        "Toulouse FC": ["Toulouse"],
        # Historical-only clubs (2014/15-2025/26 real fd.co.uk data, not in
        # the 2026-27 fixture list) -- kept so backtest data can still be
        # normalized even though they're not this season's clubs.
        "Ajaccio": ["Ajaccio"],
        "Ajaccio GFCO": ["Ajaccio GFCO"],
        "Amiens": ["Amiens"],
        "Bastia": ["Bastia"],
        "Bordeaux": ["Bordeaux"],
        "Caen": ["Caen"],
        "Clermont": ["Clermont"],
        "Dijon": ["Dijon"],
        "Evian Thonon Gaillard": ["Evian Thonon Gaillard"],
        "Guingamp": ["Guingamp"],
        "Metz": ["Metz"],
        "Montpellier": ["Montpellier"],
        "Nancy": ["Nancy"],
        "Nantes": ["Nantes"],
        "Nimes": ["Nimes"],
        "Reims": ["Reims"],
        "St Etienne": ["St Etienne"],
    },
    # Canonical spelling is fixturedownload.com's real nations-league-2026
    # feed (54 real UEFA member associations, League A/B/C/D combined),
    # cross-referenced against the-odds-api.com's live event list for the
    # same competition (soccer_uefa_nations_league) as the second real
    # source -- same discipline as every other league's table. Three real
    # spelling differences found between the two sources; all other names
    # matched exactly.
    "nations_league": {
        "Albania": [], "Andorra": [], "Armenia": [], "Austria": [], "Azerbaijan": [],
        "Belarus": [], "Belgium": [],
        "Bosnia and Herzegovina": ["Bosnia & Herzegovina"],
        "Bulgaria": [], "Croatia": [], "Cyprus": [],
        "Czechia": ["Czech Republic"],
        "Denmark": [], "England": [], "Estonia": [], "Faroe Islands": [], "Finland": [],
        "France": [], "Georgia": [], "Germany": [], "Gibraltar": [], "Greece": [],
        "Hungary": [], "Iceland": [], "Israel": [], "Italy": [], "Kazakhstan": [],
        "Kosovo": [], "Latvia": [], "Liechtenstein": [], "Lithuania": [], "Luxembourg": [],
        "Malta": [], "Moldova": [], "Montenegro": [], "Netherlands": [],
        "North Macedonia": [], "Northern Ireland": [], "Norway": [], "Poland": [],
        "Portugal": [], "Republic of Ireland": [], "Romania": [], "San Marino": [],
        "Scotland": [], "Serbia": [], "Slovakia": [], "Slovenia": [], "Spain": [],
        "Sweden": [], "Switzerland": [],
        "Türkiye": ["Turkey"],
        "Ukraine": [], "Wales": [],
    },
    # Canonical spelling is fixturedownload.com's real mls-2026 feed (30
    # real 2026 clubs, full names e.g. "Atlanta United"), cross-
    # referenced against two other real sources with their own naming
    # conventions: fixturedownload.com's own mls-2023/2024/2025 feeds
    # use SHORT city-only names (e.g. "Atlanta") for every prior season
    # -- a real, consistent convention shift at that source, not a typo
    # -- and the-odds-api.com's live event list (soccer_usa_mls) uses a
    # third convention again (e.g. "Atlanta United FC"). All three
    # confirmed directly, real aliases only.
    "mls": {
        "Atlanta United": ["Atlanta", "Atlanta United FC"],
        "Austin FC": ["Austin"],
        "CF Montréal": ["Montréal", "CF Montreal"],
        "Charlotte FC": ["Charlotte"],
        "Chicago Fire FC": ["Chicago", "Chicago Fire"],
        "Colorado Rapids": ["Colorado"],
        "Columbus Crew": ["Columbus", "Columbus Crew SC"],
        "D.C. United": ["D.C."],
        "FC Cincinnati": ["Cincinnati"],
        "FC Dallas": ["Dallas"],
        "Houston Dynamo FC": ["Houston", "Houston Dynamo"],
        "Inter Miami CF": ["Miami"],
        "LA Galaxy": ["LA"],
        "Los Angeles Football Club": ["LAFC", "Los Angeles FC"],
        "Minnesota United FC": ["Minnesota"],
        "Nashville SC": ["Nashville"],
        "New England Revolution": ["New England"],
        "New York City Football Club": ["New York City", "New York City FC"],
        "Red Bull New York": ["New York", "New York Red Bulls"],
        "Orlando City": ["Orlando", "Orlando City SC"],
        "Philadelphia Union": ["Philadelphia"],
        "Portland Timbers": ["Portland"],
        "Real Salt Lake": ["Salt Lake"],
        "San Diego FC": ["San Diego"],
        "San Jose Earthquakes": ["San Jose"],
        "Seattle Sounders FC": ["Seattle"],
        "Sporting Kansas City": ["Kansas City"],
        "St. Louis CITY SC": ["St. Louis", "St. Louis City SC"],
        "Toronto FC": ["Toronto"],
        "Vancouver Whitecaps FC": ["Vancouver"],
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
