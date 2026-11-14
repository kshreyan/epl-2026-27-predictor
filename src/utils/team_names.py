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
    # Canonical spelling is each competition's own real 2026-27
    # fixturedownload.com feed (36 current real participants per
    # competition), cross-referenced against two further real sources:
    # the-odds-api.com's live event list for the matching sport key
    # (soccer_uefa_champs_league / soccer_uefa_europa_league /
    # soccer_uefa_europa_conference_league), and fixturedownload.com's
    # own 2024-25/2025-26 feeds for the ~30-55 additional real clubs
    # that participated in a prior Swiss-model cycle but not the
    # current one (kept so the real historical backtest data can still
    # be normalized, same discipline as the domestic leagues' own
    # historical-only entries above).
    "ucl": {
        "AEK Athens": ["AEK"],
        "Ajax": [],
        "Anderlecht": [],
        "APOEL": [],
        "Arsenal": [],
        "Aston Villa": [],
        "Atalanta": [],
        "Athletic Club": ["Athletic Bilbao"],
        "Atlético Madrid": ["Atleti", "Atletico Madrid", "Atlético", "Atlético de Madrid"],
        "Antwerp": ["Royal Antwerp"],
        "Basel": ["FC Basel"],
        "Bayern Munich": ["Bayern München", "FC Bayern München", "Bayern"],
        "Benfica": [],
        "Besiktas": ["Beşiktaş"],
        "Bodø/Glimt": ["Bodo/Glimt"],
        "Bologna": [],
        "Borussia Dortmund": ["B. Dortmund", "Dortmund"],
        "Borussia Mönchengladbach": ["Mönchengladbach", "Monchengladbach"],
        "Braga": ["SC Braga"],
        "Brest": ["Stade Brestois"],
        "Barcelona": [],
        "Celtic": [],
        "Chelsea": [],
        "Club Brugge": [],
        "Como": [],
        "Copenhagen": ["FC Copenhagen"],
        "Crvena Zvezda": ["Red Star Belgrade"],
        "CSKA Moscow": ["CSKA Moskva"],
        "Dynamo Kyiv": ["FC Dynamo Kyiv"],
        "Eintracht Frankfurt": ["Frankfurt"],
        "Fenerbahce": ["Fenerbahçe"],
        "Ferencváros": ["Ferencvarosi"],
        "Feyenoord": [],
        "Galatasaray": [],
        "Genk": ["KRC Genk"],
        "Girona": [],
        "GNK Dinamo": ["Dinamo Zagreb"],
        "Inter Milan": ["Inter", "Internazionale"],
        "Istanbul Basaksehir": ["İstanbul Başakşehir"],
        "Juventus": [],
        "Kairat Almaty": [],
        "Krasnodar": ["FC Krasnodar"],
        "LASK": [],
        "Lazio": ["SS Lazio"],
        "Bayer Leverkusen": ["Leverkusen"],
        "RB Leipzig": ["Leipzig"],
        "RC Lens": ["Lens"],
        "Lille": ["LOSC"],
        "Liverpool": [],
        "Lokomotiv Moscow": ["Lokomotiv Moskva"],
        "Maccabi Haifa": ["M. Haifa"],
        "Malmö": ["Malmo FF", "Malmö FF"],
        "Manchester City": ["Man City", "Man. City"],
        "Manchester United": ["Man Utd", "Man United", "Man. United"],
        "Maribor": ["NK Maribor"],
        "Marseille": [],
        "Midtjylland": ["FC Midtjylland"],
        "AC Milan": ["Milan"],
        "Monaco": ["AS Monaco"],
        "Napoli": [],
        "Newcastle United": ["Newcastle"],
        "Olympiacos": ["Olympiakos Piraeus"],
        "Olympique Lyonnais": ["Lyon"],
        "Pafos": ["Pafos FC"],
        "Paris Saint-Germain": ["Paris", "Paris Saint Germain", "PSG"],
        "Porto": ["FC Porto"],
        "PSV Eindhoven": ["PSV"],
        "Qarabag": ["Qarabağ"],
        "Rangers": ["Glasgow Rangers"],
        "Real Betis": [],
        "Real Madrid": [],
        "Real Sociedad": [],
        "AS Roma": ["Roma"],
        "RB Salzburg": ["Salzburg"],
        "Sabah FK": ["Sabah"],
        "FC Schalke 04": ["Schalke"],
        "Sevilla FC": ["Sevilla"],
        "Shakhtar Donetsk": ["Shakhtar"],
        "Sheriff Tiraspol": ["Sheriff"],
        "Slavia Praha": [],
        "Slovan Bratislava": ["S. Bratislava", "ŠK Slovan Bratislava"],
        "Sparta Praha": ["Sparta Prague"],
        "Spartak Moscow": ["Spartak Moskva"],
        "Sporting CP": ["Sporting Lisbon"],
        "Stade Rennais FC": ["Rennes"],
        "Sturm Graz": ["SK Sturm Graz"],
        "VfB Stuttgart": ["Stuttgart"],
        "TSG Hoffenheim": ["Hoffenheim"],
        "Tottenham Hotspur": ["Tottenham"],
        "1. FC Union Berlin": ["Union Berlin"],
        "Union Saint-Gilloise": ["Union SG"],
        "Valencia CF": ["Valencia"],
        "Viking FK": ["Viking"],
        "Viktoria Plzen": ["Viktoria Plzeň", "Plzen"],
        "Villarreal": [],
        "Wolfsburg": [],
        "Young Boys": ["BSC Young Boys"],
        "Zenit": ["Zenit Saint Petersburg", "Zenit St Petersburg"],
    },
    "uel": {
        "AEK Athens": ["AEK"],
        "AEK Larnaca": [],
        "Ajax": [],
        "Anderlecht": [],
        "Antwerp": ["Royal Antwerp"],
        "APOEL": [],
        "Aris Limassol": [],
        "Arsenal": [],
        "Astana": ["FC Astana"],
        "Atalanta": [],
        "AZ Alkmaar": [],
        "FC Ararat-Armenia": ["Ararat-Armenia"],
        "Aston Villa": [],
        "Athletic Club": ["Athletic Bilbao"],
        "Barcelona": [],
        "FC Basel": ["Basel"],
        "Benfica": [],
        "Besiktas": ["Besiktas JK"],
        "Bodø/Glimt": ["Bodo/Glimt"],
        "Bologna": [],
        "Borussia Dortmund": ["Dortmund", "B. Dortmund"],
        "Borussia Mönchengladbach": ["Mönchengladbach", "Monchengladbach"],
        "SC Braga": ["Braga"],
        "Brighton & Hove Albion": ["Brighton", "Brighton and Hove Albion"],
        "Brøndby": ["Brondby"],
        "SK Brann": ["Brann"],
        "Bournemouth": [],
        "Celje": ["NK Celje"],
        "Celta Vigo": ["Celta"],
        "Celtic": [],
        "CFR Cluj": [],
        "Club Brugge": [],
        "Copenhagen": ["FC Copenhagen"],
        "Crvena Zvezda": ["Red Star Belgrade"],
        "Crystal Palace": [],
        "CSKA Moscow": ["CSKA Moskva"],
        "CSKA Sofia": ["CSKA-Sofia"],
        "Dundalk": [],
        "Dynamo Kyiv": [],
        "IF Elfsborg": ["Elfsborg"],
        "Espanyol": ["RCD Espanyol"],
        "FCSB": [],
        "Fenerbahce": ["Fenerbahçe"],
        "Ferencvaros": ["Ferencváros", "Ferencváros TC"],
        "Feyenoord": [],
        "F91 Dudelange": ["Dudelange"],
        "Eintracht Frankfurt": ["Frankfurt"],
        "SC Freiburg": ["Freiburg"],
        "Galatasaray": [],
        "Gent": ["KAA Gent"],
        "Getafe": [],
        "KRC Genk": ["Genk"],
        "GNK Dinamo": ["Dinamo Zagreb"],
        "Go Ahead Eagles": [],
        "Granada": [],
        "Häcken": ["BK Häcken"],
        "Hapoel Beer Sheva": ["H. Beer-Sheva", "Hapoel Be'er Sheva"],
        "HJK Helsinki": ["HJK"],
        "TSG Hoffenheim": ["Hoffenheim"],
        "Inter Milan": ["Inter", "Internazionale"],
        "Istanbul Basaksehir": ["İstanbul Başakşehir"],
        "Jagiellonia Bialystok": ["Jagiellonia", "Jagiellonia Białystok"],
        "Juventus": [],
        "Krasnodar": ["FC Krasnodar"],
        "LASK": [],
        "Lazio": [],
        "Lech Poznan": ["Lech Poznań", "Lech"],
        "RB Leipzig": ["Leipzig"],
        "RC Lens": ["Lens"],
        "Bayer Leverkusen": ["Leverkusen"],
        "Legia Warsaw": ["Legia"],
        "Leicester City": ["Leicester"],
        "Levski Sofia": ["PFC Levski Sofia"],
        "Liberec": ["Slovan Liberec"],
        "Lille": ["LOSC"],
        "Lillestrom": ["Lillestrøm"],
        "Liverpool": [],
        "Lokomotiv Moscow": ["Lokomotiv Moskva"],
        "Ludogorets": ["Ludogorets Razgrad"],
        "Lugano": ["FC Lugano"],
        "Lyon": [],
        "Maccabi Haifa": ["M. Haifa"],
        "Maccabi Tel Aviv": ["M. Tel-Aviv"],
        "Malmo": ["Malmö"],
        "Manchester United": ["Man Utd", "Man United", "Man. United"],
        "Marseille": [],
        "AC Milan": ["Milan"],
        "FC Midtjylland": ["Midtjylland"],
        "Molde": ["Molde FK"],
        "Monaco": ["AS Monaco"],
        "N.E.C.": ["NEC Nijmegen"],
        "Nantes": ["FC Nantes"],
        "Napoli": [],
        "Nice": ["OGC Nice"],
        "Nottingham Forest": ["Nott'm Forest"],
        "OFI Crete": [],
        "Oleksandriya": ["Olexandriya"],
        "Olympiacos": ["Olympiakos Piraeus"],
        "Omonia": ["Omonoia FC", "Omonoia"],
        "PAOK": [],
        "Panathinaikos": ["Panathinaikos FC"],
        "Partizan": ["Partizan Belgrade"],
        "Porto": [],
        "PSV Eindhoven": ["PSV"],
        "Qarabag": ["Qarabağ"],
        "Rakow Czestochowa": ["Raków", "Rakow", "Raków Częstochowa"],
        "Rangers": [],
        "Rapid Wien": ["Rapid Vienna"],
        "Real Betis": ["Betis"],
        "Real Sociedad": [],
        "Rennes": [],
        "FK RFS": ["RFS"],
        "Rijeka": ["HNK Rijeka"],
        "AS Roma": ["Roma"],
        "Rosenborg": ["Rosenborg BK"],
        "RB Salzburg": ["Salzburg"],
        "Saint-Étienne": ["St-Étienne", "AS Saint-Étienne"],
        "Servette": ["Servette FC"],
        "Sevilla FC": ["Sevilla"],
        "Shakhtar Donetsk": ["Shakhtar"],
        "Sheriff Tiraspol": ["Sheriff"],
        "Sivasspor": [],
        "Slavia Praha": [],
        "Slovan Bratislava": ["S. Bratislava"],
        "Sparta Praha": ["Sparta Prague"],
        "Spartak Moscow": ["Spartak Moskva"],
        "Sporting CP": ["Sporting Lisbon"],
        "Standard Liège": ["Standard Liege"],
        "Sturm Graz": ["SK Sturm Graz", "Sturm"],
        "Sunderland": [],
        "VfB Stuttgart": ["Stuttgart"],
        "TSC Bačka Topola": ["TSC"],
        "Tottenham Hotspur": ["Tottenham"],
        "Torreense": [],
        "Toulouse": ["FC Toulouse", "Toulouse FC"],
        "Trabzonspor": [],
        "FC Twente": ["Twente"],
        "1. FC Union Berlin": ["Union Berlin"],
        "Union Saint-Gilloise": ["Union SG"],
        "FC Utrecht": ["Utrecht"],
        "Viktoria Plzen": ["Viktoria Plzeň"],
        "Villarreal": [],
        "Vitória SC": ["Vitória Guimarães", "Vitoria SC"],
        "West Ham United": ["West Ham"],
        "Wolfsberger AC": ["Wolfsberg", "WAC"],
        "Wolfsburg": [],
        "Wolverhampton Wanderers": ["Wolves"],
        "Young Boys": ["BSC Young Boys"],
        "Zenit": ["Zenit Saint Petersburg"],
        "Zorya Luhansk": [],
        "Zürich": ["FC Zürich"],
    },
    "nfl": {
        "Arizona Cardinals": [], "Atlanta Falcons": [], "Baltimore Ravens": [],
        "Buffalo Bills": [], "Carolina Panthers": [], "Chicago Bears": [],
        "Cincinnati Bengals": [], "Cleveland Browns": [], "Dallas Cowboys": [],
        "Denver Broncos": [], "Detroit Lions": [], "Green Bay Packers": [],
        "Houston Texans": [], "Indianapolis Colts": [], "Jacksonville Jaguars": [],
        "Kansas City Chiefs": [], "Las Vegas Raiders": [], "Los Angeles Chargers": [],
        "Los Angeles Rams": [], "Miami Dolphins": [], "Minnesota Vikings": [],
        "New England Patriots": [], "New Orleans Saints": [], "New York Giants": [],
        "New York Jets": [], "Philadelphia Eagles": [], "Pittsburgh Steelers": [],
        "San Francisco 49ers": [], "Seattle Seahawks": [], "Tampa Bay Buccaneers": [],
        "Tennessee Titans": [],
        # Real historical name: ESPN's own schedule data uses the short
        # "Washington" (not "Washington Commanders") for this team in
        # several real past seasons -- confirmed directly across 2021-2026.
        "Washington Commanders": ["Washington"],
    },
    # Canonical spelling is ESPN's own team displayName, same discipline
    # as "nfl" above. Cross-referenced directly against The Odds API's
    # live event list (basketball_nba): one real spelling difference
    # found (ESPN's short "LA Clippers" vs the Odds API's full "Los
    # Angeles Clippers"); every other team matched exactly.
    "nba": {
        "Atlanta Hawks": [], "Boston Celtics": [], "Brooklyn Nets": [],
        "Charlotte Hornets": [], "Chicago Bulls": [], "Cleveland Cavaliers": [],
        "Dallas Mavericks": [], "Denver Nuggets": [], "Detroit Pistons": [],
        "Golden State Warriors": [], "Houston Rockets": [], "Indiana Pacers": [],
        "LA Clippers": ["Los Angeles Clippers"], "Los Angeles Lakers": [],
        "Memphis Grizzlies": [], "Miami Heat": [], "Milwaukee Bucks": [],
        "Minnesota Timberwolves": [], "New Orleans Pelicans": [], "New York Knicks": [],
        "Oklahoma City Thunder": [], "Orlando Magic": [], "Philadelphia 76ers": [],
        "Phoenix Suns": [], "Portland Trail Blazers": [], "Sacramento Kings": [],
        "San Antonio Spurs": [], "Toronto Raptors": [], "Utah Jazz": [],
        "Washington Wizards": [],
    },
    # Canonical spelling is ESPN's own team displayName, same discipline
    # as the other American team sports above -- generated directly
    # from ESPN's own real, live FBS conference standings this session
    # (espn_api.py's fetch_real_college_conferences("ncaaf"), 138 real teams, see
    # config/leagues.yaml's note on why this roster isn't a fixed
    # closed set the way NFL/NBA's is). Not cross-referenced
    # against The Odds API team-by-team the way the smaller closed
    # rosters above were -- 138 teams makes that impractical by hand;
    # a real Odds API spelling mismatch for any one team surfaces as
    # that one fixture simply getting no real market odds (the same
    # "flagged unavailable, never guessed" fallback collect_odds.py
    # already uses everywhere), not a silent wrong number.
    "ncaaf": {
        "Air Force Falcons": [], "Akron Zips": [], "Alabama Crimson Tide": [],
        "App State Mountaineers": [], "Arizona State Sun Devils": [], "Arizona Wildcats": [],
        "Arkansas Razorbacks": [], "Arkansas State Red Wolves": [], "Army Black Knights": [],
        "Auburn Tigers": [], "BYU Cougars": [], "Ball State Cardinals": [],
        "Baylor Bears": [], "Boise State Broncos": [], "Boston College Eagles": [],
        "Bowling Green Falcons": [], "Buffalo Bulls": [], "California Golden Bears": [],
        "Central Michigan Chippewas": [], "Charlotte 49ers": [], "Cincinnati Bearcats": [],
        "Clemson Tigers": [], "Coastal Carolina Chanticleers": [], "Colorado Buffaloes": [],
        "Colorado State Rams": [], "Delaware Blue Hens": [], "Duke Blue Devils": [],
        "East Carolina Pirates": [], "Eastern Michigan Eagles": [],
        "Florida Atlantic Owls": [], "Florida Gators": [],
        "Florida International Panthers": [], "Florida State Seminoles": [],
        "Fresno State Bulldogs": [], "Georgia Bulldogs": [], "Georgia Southern Eagles": [],
        "Georgia State Panthers": [], "Georgia Tech Yellow Jackets": [],
        "Hawai'i Rainbow Warriors": [], "Houston Cougars": [], "Illinois Fighting Illini": [],
        "Indiana Hoosiers": [], "Iowa Hawkeyes": [], "Iowa State Cyclones": [],
        "Jacksonville State Gamecocks": [], "James Madison Dukes": [], "Kansas Jayhawks": [],
        "Kansas State Wildcats": [], "Kennesaw State Owls": [],
        "Kent State Golden Flashes": [], "Kentucky Wildcats": [], "LSU Tigers": [],
        "Liberty Flames": [], "Louisiana Ragin' Cajuns": [], "Louisiana Tech Bulldogs": [],
        "Louisville Cardinals": [], "Marshall Thundering Herd": [], "Maryland Terrapins": [],
        "Massachusetts Minutemen": [], "Memphis Tigers": [], "Miami (OH) RedHawks": [],
        "Miami Hurricanes": [], "Michigan State Spartans": [], "Michigan Wolverines": [],
        "Middle Tennessee Blue Raiders": [], "Minnesota Golden Gophers": [],
        "Mississippi State Bulldogs": [], "Missouri State Bears": [], "Missouri Tigers": [],
        "NC State Wolfpack": [], "Navy Midshipmen": [], "Nebraska Cornhuskers": [],
        "Nevada Wolf Pack": [], "New Mexico Lobos": [], "New Mexico State Aggies": [],
        "North Carolina Tar Heels": [], "North Dakota State Bison": [],
        "North Texas Mean Green": [], "Northern Illinois Huskies": [],
        "Northwestern Wildcats": [], "Notre Dame Fighting Irish": [], "Ohio Bobcats": [],
        "Ohio State Buckeyes": [], "Oklahoma Sooners": [], "Oklahoma State Cowboys": [],
        "Old Dominion Monarchs": [], "Ole Miss Rebels": [], "Oregon Ducks": [],
        "Oregon State Beavers": [], "Penn State Nittany Lions": [], "Pittsburgh Panthers": [],
        "Purdue Boilermakers": [], "Rice Owls": [], "Rutgers Scarlet Knights": [],
        "SMU Mustangs": [], "Sacramento State Hornets": [], "Sam Houston Bearkats": [],
        "San Diego State Aztecs": [], "San José State Spartans": [],
        "South Alabama Jaguars": [], "South Carolina Gamecocks": [],
        "South Florida Bulls": [], "Southern Miss Golden Eagles": [], "Stanford Cardinal": [],
        "Syracuse Orange": [], "TCU Horned Frogs": [], "Temple Owls": [],
        "Tennessee Volunteers": [], "Texas A&M Aggies": [], "Texas Longhorns": [],
        "Texas State Bobcats": [], "Texas Tech Red Raiders": [], "Toledo Rockets": [],
        "Troy Trojans": [], "Tulane Green Wave": [], "Tulsa Golden Hurricane": [],
        "UAB Blazers": [], "UCF Knights": [], "UCLA Bruins": [], "UConn Huskies": [],
        "UL Monroe Warhawks": [], "UNLV Rebels": [], "USC Trojans": [], "UTEP Miners": [],
        "UTSA Roadrunners": [], "Utah State Aggies": [], "Utah Utes": [],
        "Vanderbilt Commodores": [], "Virginia Cavaliers": [], "Virginia Tech Hokies": [],
        "Wake Forest Demon Deacons": [], "Washington Huskies": [],
        "Washington State Cougars": [], "West Virginia Mountaineers": [],
        "Western Kentucky Hilltoppers": [], "Western Michigan Broncos": [],
        "Wisconsin Badgers": [], "Wyoming Cowboys": [],
    },
    # Canonical spelling is ESPN's own team displayName, same discipline
    # as "ncaaf" above -- generated directly from ESPN's own real, live
    # Division I conference standings this session
    # (espn_api.py's fetch_real_college_conferences("ncaab"), 365 real
    # teams, see config/leagues.yaml's note on why this roster isn't a
    # fixed closed set the way NFL/NBA's is). Not cross-referenced
    # against The Odds API team-by-team the way the smaller closed
    # rosters above were -- 365 teams makes that impractical by hand;
    # a real Odds API spelling mismatch for any one team surfaces as
    # that one fixture simply getting no real market odds (the same
    # "flagged unavailable, never guessed" fallback collect_odds.py
    # already uses everywhere), not a silent wrong number.
    "ncaab": {
        "Abilene Christian Wildcats": [], "Air Force Falcons": [], "Akron Zips": [],
        "Alabama A&M Bulldogs": [], "Alabama Crimson Tide": [],
        "Alabama State Hornets": [], "Alcorn State Braves": [],
        "American University Eagles": [], "App State Mountaineers": [],
        "Arizona State Sun Devils": [], "Arizona Wildcats": [],
        "Arkansas Razorbacks": [], "Arkansas State Red Wolves": [],
        "Arkansas-Pine Bluff Golden Lions": [], "Army Black Knights": [],
        "Auburn Tigers": [], "Austin Peay Governors": [], "BYU Cougars": [],
        "Ball State Cardinals": [], "Baylor Bears": [], "Bellarmine Knights": [],
        "Belmont Bruins": [], "Bethune-Cookman Wildcats": [],
        "Binghamton Bearcats": [], "Boise State Broncos": [],
        "Boston College Eagles": [], "Boston University Terriers": [],
        "Bowling Green Falcons": [], "Bradley Braves": [], "Brown Bears": [],
        "Bryant Bulldogs": [], "Bucknell Bison": [], "Buffalo Bulls": [],
        "Butler Bulldogs": [], "Cal Poly Mustangs": [],
        "Cal State Bakersfield Roadrunners": [], "Cal State Fullerton Titans": [],
        "Cal State Northridge Matadors": [], "California Baptist Lancers": [],
        "California Golden Bears": [], "Campbell Fighting Camels": [],
        "Canisius Golden Griffins": [], "Central Arkansas Bears": [],
        "Central Connecticut Blue Devils": [], "Central Michigan Chippewas": [],
        "Charleston Cougars": [], "Charleston Southern Buccaneers": [],
        "Charlotte 49ers": [], "Chattanooga Mocs": [], "Chicago State Cougars": [],
        "Cincinnati Bearcats": [], "Clemson Tigers": [], "Cleveland State Vikings": [],
        "Coastal Carolina Chanticleers": [], "Colgate Raiders": [],
        "Colorado Buffaloes": [], "Colorado State Rams": [], "Columbia Lions": [],
        "Coppin State Eagles": [], "Cornell Big Red": [], "Creighton Bluejays": [],
        "Dartmouth Big Green": [], "Davidson Wildcats": [], "Dayton Flyers": [],
        "DePaul Blue Demons": [], "Delaware Blue Hens": [],
        "Delaware State Hornets": [], "Denver Pioneers": [],
        "Detroit Mercy Titans": [], "Drake Bulldogs": [], "Drexel Dragons": [],
        "Duke Blue Devils": [], "Duquesne Dukes": [], "East Carolina Pirates": [],
        "East Tennessee State Buccaneers": [], "East Texas A&M Lions": [],
        "Eastern Illinois Panthers": [], "Eastern Kentucky Colonels": [],
        "Eastern Michigan Eagles": [], "Eastern Washington Eagles": [],
        "Elon Phoenix": [], "Evansville Purple Aces": [], "Fairfield Stags": [],
        "Fairleigh Dickinson Knights": [], "Florida A&M Rattlers": [],
        "Florida Atlantic Owls": [], "Florida Gators": [],
        "Florida Gulf Coast Eagles": [], "Florida International Panthers": [],
        "Florida State Seminoles": [], "Fordham Rams": [], "Fresno State Bulldogs": [],
        "Furman Paladins": [], "Gardner-Webb Runnin' Bulldogs": [],
        "George Mason Patriots": [], "George Washington Revolutionaries": [],
        "Georgetown Hoyas": [], "Georgia Bulldogs": [], "Georgia Southern Eagles": [],
        "Georgia State Panthers": [], "Georgia Tech Yellow Jackets": [],
        "Gonzaga Bulldogs": [], "Grambling Tigers": [], "Grand Canyon Lopes": [],
        "Green Bay Phoenix": [], "Hampton Pirates": [], "Harvard Crimson": [],
        "Hawai'i Rainbow Warriors": [], "High Point Panthers": [], "Hofstra Pride": [],
        "Holy Cross Crusaders": [], "Houston Christian Huskies": [],
        "Houston Cougars": [], "Howard Bison": [], "IU Indianapolis Jaguars": [],
        "Idaho State Bengals": [], "Idaho Vandals": [], "Illinois Fighting Illini": [],
        "Illinois State Redbirds": [], "Incarnate Word Cardinals": [],
        "Indiana Hoosiers": [], "Indiana State Sycamores": [], "Iona Gaels": [],
        "Iowa Hawkeyes": [], "Iowa State Cyclones": [], "Jackson State Tigers": [],
        "Jacksonville Dolphins": [], "Jacksonville State Gamecocks": [],
        "James Madison Dukes": [], "Kansas City Roos": [], "Kansas Jayhawks": [],
        "Kansas State Wildcats": [], "Kennesaw State Owls": [],
        "Kent State Golden Flashes": [], "Kentucky Wildcats": [],
        "LSU New Orleans Privateers": [], "LSU Tigers": [], "La Salle Explorers": [],
        "Lafayette Leopards": [], "Lamar Cardinals": [], "Le Moyne Dolphins": [],
        "Lehigh Mountain Hawks": [], "Liberty Flames": [], "Lindenwood Lions": [],
        "Lipscomb Bisons": [], "Little Rock Trojans": [], "Long Beach State Beach": [],
        "Long Island University Sharks": [], "Longwood Lancers": [],
        "Louisiana Ragin' Cajuns": [], "Louisiana Tech Bulldogs": [],
        "Louisville Cardinals": [], "Loyola Chicago Ramblers": [],
        "Loyola Maryland Greyhounds": [], "Loyola Marymount Lions": [],
        "Maine Black Bears": [], "Manhattan Jaspers": [], "Marist Red Foxes": [],
        "Marquette Golden Eagles": [], "Marshall Thundering Herd": [],
        "Maryland Eastern Shore Hawks": [], "Maryland Terrapins": [],
        "Massachusetts Minutemen": [], "McNeese Cowboys": [], "Memphis Tigers": [],
        "Mercer Bears": [], "Mercyhurst Lakers": [], "Merrimack Warriors": [],
        "Miami (OH) RedHawks": [], "Miami Hurricanes": [],
        "Michigan State Spartans": [], "Michigan Wolverines": [],
        "Middle Tennessee Blue Raiders": [], "Milwaukee Panthers": [],
        "Minnesota Golden Gophers": [], "Mississippi State Bulldogs": [],
        "Mississippi Valley State Delta Devils": [], "Missouri State Bears": [],
        "Missouri Tigers": [], "Monmouth Hawks": [], "Montana Grizzlies": [],
        "Montana State Bobcats": [], "Morehead State Eagles": [],
        "Morgan State Bears": [], "Mount St. Mary's Mountaineers": [],
        "Murray State Racers": [], "NC State Wolfpack": [], "NJIT Highlanders": [],
        "Navy Midshipmen": [], "Nebraska Cornhuskers": [], "Nevada Wolf Pack": [],
        "New Hampshire Wildcats": [], "New Haven Chargers": [], "New Mexico Lobos": [],
        "New Mexico State Aggies": [], "Niagara Purple Eagles": [],
        "Nicholls Colonels": [], "Norfolk State Spartans": [],
        "North Alabama Lions": [], "North Carolina A&T Aggies": [],
        "North Carolina Central Eagles": [], "North Carolina Tar Heels": [],
        "North Dakota Fighting Hawks": [], "North Dakota State Bison": [],
        "North Florida Ospreys": [], "North Texas Mean Green": [],
        "Northeastern Huskies": [], "Northern Arizona Lumberjacks": [],
        "Northern Colorado Bears": [], "Northern Illinois Huskies": [],
        "Northern Iowa Panthers": [], "Northern Kentucky Norse": [],
        "Northwestern State Demons": [], "Northwestern Wildcats": [],
        "Notre Dame Fighting Irish": [], "Oakland Golden Grizzlies": [],
        "Ohio Bobcats": [], "Ohio State Buckeyes": [], "Oklahoma Sooners": [],
        "Oklahoma State Cowboys": [], "Old Dominion Monarchs": [],
        "Ole Miss Rebels": [], "Omaha Mavericks": [], "Oral Roberts Golden Eagles": [],
        "Oregon Ducks": [], "Oregon State Beavers": [], "Pacific Tigers": [],
        "Penn State Nittany Lions": [], "Pennsylvania Quakers": [],
        "Pepperdine Waves": [], "Pittsburgh Panthers": [], "Portland Pilots": [],
        "Portland State Vikings": [], "Prairie View A&M Panthers": [],
        "Presbyterian Blue Hose": [], "Princeton Tigers": [], "Providence Friars": [],
        "Purdue Boilermakers": [], "Purdue Fort Wayne Mastodons": [],
        "Queens University Royals": [], "Quinnipiac Bobcats": [],
        "Radford Highlanders": [], "Rhode Island Rams": [], "Rice Owls": [],
        "Richmond Spiders": [], "Rider Broncs": [], "Robert Morris Colonials": [],
        "Rutgers Scarlet Knights": [], "SE Louisiana Lions": [],
        "SIU Edwardsville Cougars": [], "SMU Mustangs": [],
        "Sacramento State Hornets": [], "Sacred Heart Pioneers": [],
        "Saint Joseph's Hawks": [], "Saint Louis Billikens": [],
        "Saint Mary's Gaels": [], "Saint Peter's Peacocks": [],
        "Sam Houston Bearkats": [], "Samford Bulldogs": [],
        "San Diego State Aztecs": [], "San Diego Toreros": [],
        "San Francisco Dons": [], "San José State Spartans": [],
        "Santa Clara Broncos": [], "Seattle U Redhawks": [], "Seton Hall Pirates": [],
        "Siena Saints": [], "South Alabama Jaguars": [],
        "South Carolina Gamecocks": [], "South Carolina State Bulldogs": [],
        "South Carolina Upstate Spartans": [], "South Dakota Coyotes": [],
        "South Dakota State Jackrabbits": [], "South Florida Bulls": [],
        "Southeast Missouri State Redhawks": [], "Southern Illinois Salukis": [],
        "Southern Indiana Screaming Eagles": [], "Southern Jaguars": [],
        "Southern Miss Golden Eagles": [], "Southern Utah Thunderbirds": [],
        "St. Bonaventure Bonnies": [], "St. John's Red Storm": [],
        "St. Thomas Tommies": [], "Stanford Cardinal": [],
        "Stephen F. Austin Lumberjacks": [], "Stetson Hatters": [],
        "Stonehill Skyhawks": [], "Stony Brook Seawolves": [], "Syracuse Orange": [],
        "TCU Horned Frogs": [], "Tarleton State Texans": [], "Temple Owls": [],
        "Tennessee State Tigers": [], "Tennessee Tech Golden Eagles": [],
        "Tennessee Volunteers": [], "Texas A&M Aggies": [],
        "Texas A&M-Corpus Christi Islanders": [], "Texas Longhorns": [],
        "Texas Southern Tigers": [], "Texas State Bobcats": [],
        "Texas Tech Red Raiders": [], "The Citadel Bulldogs": [], "Toledo Rockets": [],
        "Towson Tigers": [], "Troy Trojans": [], "Tulane Green Wave": [],
        "Tulsa Golden Hurricane": [], "UAB Blazers": [], "UAlbany Great Danes": [],
        "UC Davis Aggies": [], "UC Irvine Anteaters": [],
        "UC Riverside Highlanders": [], "UC San Diego Tritons": [],
        "UC Santa Barbara Gauchos": [], "UCF Knights": [], "UCLA Bruins": [],
        "UConn Huskies": [], "UIC Flames": [], "UL Monroe Warhawks": [],
        "UMBC Retrievers": [], "UMass Lowell River Hawks": [],
        "UNC Asheville Bulldogs": [], "UNC Greensboro Spartans": [],
        "UNC Wilmington Seahawks": [], "UNLV Rebels": [], "USC Trojans": [],
        "UT Arlington Mavericks": [], "UT Martin Skyhawks": [],
        "UT Rio Grande Valley Vaqueros": [], "UTEP Miners": [], "UTSA Roadrunners": [],
        "Utah State Aggies": [], "Utah Tech Trailblazers": [], "Utah Utes": [],
        "Utah Valley Wolverines": [], "VCU Rams": [], "VMI Keydets": [],
        "Valparaiso Beacons": [], "Vanderbilt Commodores": [],
        "Vermont Catamounts": [], "Villanova Wildcats": [], "Virginia Cavaliers": [],
        "Virginia Tech Hokies": [], "Wagner Seahawks": [],
        "Wake Forest Demon Deacons": [], "Washington Huskies": [],
        "Washington State Cougars": [], "Weber State Wildcats": [],
        "West Florida Argonauts": [], "West Georgia Wolves": [],
        "West Virginia Mountaineers": [], "Western Carolina Catamounts": [],
        "Western Illinois Leathernecks": [], "Western Kentucky Hilltoppers": [],
        "Western Michigan Broncos": [], "Wichita State Shockers": [],
        "William & Mary Tribe": [], "Winthrop Eagles": [], "Wisconsin Badgers": [],
        "Wofford Terriers": [], "Wright State Raiders": [], "Wyoming Cowboys": [],
        "Xavier Musketeers": [], "Yale Bulldogs": [], "Youngstown State Penguins": [],
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


def is_known_team(raw_name: str, league_id: str) -> bool:
    """True if `raw_name` resolves to a known canonical team/alias for
    this league -- a non-raising check for callers that need to skip a
    real but out-of-scope opponent (e.g. an FCS "buy game" opponent on
    an NCAA Football FBS team's real schedule) rather than treat it as
    a data error the way normalize_team_name's KeyError does."""
    table = _ALIAS_TO_CANONICAL.get(league_id, {})
    return raw_name.strip().lower() in table


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
