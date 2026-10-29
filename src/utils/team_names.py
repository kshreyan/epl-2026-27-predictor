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
        "AEK Athens": [],
        "Ajax": [],
        "Arsenal": [],
        "Aston Villa": [],
        "Atalanta": [],
        "Athletic Club": ["Athletic Bilbao"],
        "Atlético Madrid": ["Atleti", "Atletico Madrid"],
        "Bayern Munich": ["Bayern München", "FC Bayern München"],
        "Benfica": [],
        "Bodø/Glimt": ["Bodo/Glimt"],
        "Bologna": [],
        "Borussia Dortmund": ["B. Dortmund"],
        "Brest": ["Stade Brestois"],
        "Barcelona": [],
        "Celtic": [],
        "Chelsea": [],
        "Club Brugge": [],
        "Como": [],
        "Copenhagen": ["FC Copenhagen"],
        "Crvena Zvezda": ["Red Star Belgrade"],
        "Eintracht Frankfurt": ["Frankfurt"],
        "Fenerbahce": ["Fenerbahçe"],
        "Feyenoord": [],
        "Galatasaray": [],
        "Girona": [],
        "GNK Dinamo": ["Dinamo Zagreb"],
        "Inter Milan": ["Inter"],
        "Juventus": [],
        "Kairat Almaty": [],
        "LASK": [],
        "Bayer Leverkusen": ["Leverkusen"],
        "RB Leipzig": ["Leipzig"],
        "RC Lens": ["Lens"],
        "Lille": [],
        "Liverpool": [],
        "Manchester City": ["Man City"],
        "Manchester United": ["Man Utd"],
        "Marseille": [],
        "AC Milan": ["Milan"],
        "Monaco": ["AS Monaco"],
        "Napoli": [],
        "Newcastle United": ["Newcastle"],
        "Olympiacos": ["Olympiakos Piraeus"],
        "Pafos": ["Pafos FC"],
        "Paris Saint-Germain": ["Paris", "Paris Saint Germain", "PSG"],
        "Porto": [],
        "PSV Eindhoven": ["PSV"],
        "Qarabag": ["Qarabağ"],
        "Real Betis": [],
        "Real Madrid": [],
        "AS Roma": ["Roma"],
        "RB Salzburg": ["Salzburg"],
        "Sabah FK": ["Sabah"],
        "Shakhtar Donetsk": ["Shakhtar"],
        "Slavia Praha": [],
        "Slovan Bratislava": ["S. Bratislava", "ŠK Slovan Bratislava"],
        "Sparta Praha": ["Sparta Prague"],
        "Sporting CP": ["Sporting Lisbon"],
        "Sturm Graz": ["SK Sturm Graz"],
        "VfB Stuttgart": ["Stuttgart"],
        "Tottenham Hotspur": ["Tottenham"],
        "Union Saint-Gilloise": ["Union SG"],
        "Viking FK": ["Viking"],
        "Villarreal": [],
        "Young Boys": ["BSC Young Boys"],
    },
    "uel": {
        "Ajax": [],
        "Anderlecht": [],
        "AZ Alkmaar": [],
        "FC Ararat-Armenia": ["Ararat-Armenia"],
        "Aston Villa": [],
        "Athletic Club": ["Athletic Bilbao"],
        "FC Basel": ["Basel"],
        "Benfica": [],
        "Besiktas": ["Besiktas JK"],
        "Bodø/Glimt": ["Bodo/Glimt"],
        "Bologna": [],
        "SC Braga": ["Braga"],
        "SK Brann": ["Brann"],
        "Bournemouth": [],
        "Celje": ["NK Celje"],
        "Celta Vigo": ["Celta"],
        "Celtic": [],
        "Crvena Zvezda": ["Red Star Belgrade"],
        "Crystal Palace": [],
        "Dynamo Kyiv": [],
        "IF Elfsborg": ["Elfsborg"],
        "FCSB": [],
        "Fenerbahce": ["Fenerbahçe"],
        "Ferencvaros": ["Ferencváros", "Ferencváros TC"],
        "Feyenoord": [],
        "Eintracht Frankfurt": ["Frankfurt"],
        "SC Freiburg": ["Freiburg"],
        "Galatasaray": [],
        "KRC Genk": ["Genk"],
        "GNK Dinamo": ["Dinamo Zagreb"],
        "Go Ahead Eagles": [],
        "Hapoel Beer Sheva": ["H. Beer-Sheva", "Hapoel Be'er Sheva"],
        "TSG Hoffenheim": ["Hoffenheim"],
        "Jagiellonia Bialystok": ["Jagiellonia", "Jagiellonia Białystok"],
        "Juventus": [],
        "Lazio": [],
        "Lech Poznan": ["Lech Poznań"],
        "Bayer Leverkusen": ["Leverkusen"],
        "Levski Sofia": ["PFC Levski Sofia"],
        "Lille": [],
        "Lillestrom": ["Lillestrøm"],
        "Ludogorets": ["Ludogorets Razgrad"],
        "Lyon": [],
        "Maccabi Tel Aviv": ["M. Tel-Aviv"],
        "Malmo": ["Malmö"],
        "Manchester United": ["Man Utd"],
        "Marseille": [],
        "AC Milan": ["Milan"],
        "FC Midtjylland": ["Midtjylland"],
        "N.E.C.": ["NEC Nijmegen"],
        "Nice": ["OGC Nice"],
        "Nottingham Forest": ["Nott'm Forest"],
        "OFI Crete": [],
        "Olympiacos": ["Olympiakos Piraeus"],
        "Omonia": ["Omonoia FC", "Omonoia"],
        "PAOK": [],
        "Panathinaikos": ["Panathinaikos FC"],
        "Porto": [],
        "Qarabag": ["Qarabağ"],
        "Rangers": [],
        "Real Betis": [],
        "Real Sociedad": [],
        "Rennes": [],
        "FK RFS": ["RFS"],
        "AS Roma": ["Roma"],
        "RB Salzburg": ["Salzburg"],
        "Slavia Praha": [],
        "Sparta Praha": ["Sparta Prague"],
        "Sturm Graz": ["SK Sturm Graz"],
        "Sunderland": [],
        "VfB Stuttgart": ["Stuttgart"],
        "Tottenham Hotspur": ["Tottenham"],
        "Torreense": [],
        "FC Twente": ["Twente"],
        "Union Saint-Gilloise": ["Union SG"],
        "FC Utrecht": ["Utrecht"],
        "Viktoria Plzen": ["Viktoria Plzeň"],
        "Young Boys": ["BSC Young Boys"],
    },
    "uecl": {
        "AEK Athens": [],
        "AEK Larnaca": [],
        "Aberdeen": [],
        "AGF Aarhus": ["Aarhus"],
        "Ajax": [],
        "APOEL": [],
        "FC Astana": ["Astana"],
        "Atalanta": ["Atalanta BC"],
        "AZ Alkmaar": [],
        "Istanbul Basaksehir": ["Basaksehir", "Başakşehir"],
        "Borac Banja Luka": ["Borac", "FK Borac Banja Luka"],
        "SC Braga": ["Braga"],
        "SK Brann": ["Brann"],
        "Breidablik": ["Breiðablik"],
        "Brighton": ["Brighton and Hove Albion"],
        "Cercle Brugge": [],
        "Celje": ["NK Celje"],
        "Chelsea": [],
        "CSKA Sofia": ["PFC CSKA Sofia"],
        "FC Copenhagen": ["Copenhagen"],
        "Crvena Zvezda": ["Red Star Belgrade"],
        "Crystal Palace": [],
        "Dinamo Minsk": ["Dinamo-Minsk", "FC Dinamo Minsk"],
        "Djurgarden": ["Djurgården", "Djurgårdens IF"],
        "KF Drita": ["Drita"],
        "Dynamo Kyiv": [],
        "KF Egnatia": ["Egnatia"],
        "Fiorentina": [],
        "SC Freiburg": ["Freiburg"],
        "Gent": [],
        "Getafe": [],
        "Hajduk Split": [],
        "Hamrun Spartans": [],
        "1. FC Heidenheim": ["Heidenheim"],
        "Hearts": [],
        "HJK Helsinki": ["HJK"],
        "Hacken": ["Häcken", "BK Häcken"],
        "FC Iberia 1999": ["Iberia Tbilisi"],
        "Inter Club d'Escaldes": ["Inter Escaldes"],
        "Jablonec": ["FK Jablonec"],
        "Jagiellonia Bialystok": ["Jagiellonia", "Jagiellonia Białystok"],
        "FC Kairat": ["Kairat Almaty"],
        "Kauno Zalgiris": ["Kauno Žalgiris", "FK Kauno Žalgiris"],
        "KuPS Kuopio": [],
        "LASK": [],
        "Larne": [],
        "Lausanne-Sport": ["FC Lausanne-Sport"],
        "Lech Poznan": ["Lech Poznań"],
        "Legia Warszawa": ["Legia Warsaw"],
        "Lincoln Red Imps": ["L. Red Imps", "Lincoln Red Imps FC"],
        "FC Lugano": ["Lugano"],
        "1. FSV Mainz 05": ["Mainz"],
        "FC Midtjylland": ["Midtjylland"],
        "Mjallby": ["Mjällby", "Mjällby AIF"],
        "Mlada Boleslav": ["Mladá Boleslav", "FK Mladá Boleslav"],
        "Molde": ["Molde FK"],
        "AS Monaco": ["Monaco"],
        "FC Noah": ["Noah"],
        "FC Nordsjaelland": ["Nordsjælland", "Nordsjaelland"],
        "NK Olimpija Ljubljana": ["Olimpija"],
        "Omonia": ["Omonoia"],
        "Pafos": ["Pafos FC"],
        "Panathinaikos": ["Panathinaikos FC"],
        "FC Petrocub": ["Petrocub"],
        "Rakow Czestochowa": ["Raków", "Rakow", "Raków Częstochowa"],
        "Rayo Vallecano": [],
        "Real Betis": [],
        "Riga FC": ["Riga"],
        "HNK Rijeka": ["Rijeka"],
        "Rapid Wien": ["SK Rapid"],
        "Samsunspor": [],
        "Shakhtar Donetsk": ["Shakhtar"],
        "Shamrock Rovers": [],
        "Shelbourne": [],
        "KF Shkendija": ["Shkëndija", "Shkendija", "KF Shkëndija"],
        "Sigma Olomouc": [],
        "Sint-Truidense": ["Sint Truiden"],
        "Slovan Bratislava": ["S. Bratislava", "ŠK Slovan Bratislava"],
        "Sparta Praha": [],
        "FC St. Gallen": ["St. Gallen"],
        "RC Strasbourg": ["Strasbourg"],
        "FK TSC": ["TSC"],
        "The New Saints": [],
        "FC Thun": ["Thun"],
        "Trabzonspor": [],
        "FC Twente": ["Twente", "FC Twente Enschede"],
        "Universitatea Craiova": ["U. Craiova"],
        "Vikingur Reykjavik": ["Víkingur R."],
        "Vitoria SC": ["Vitória SC", "Vitória Guimarães"],
        "HSK Zrinjski": ["Zrinjski", "HŠK Zrinjski Mostar"],
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
    # (espn_api.py's fetch_real_fbs_conferences(), 138 real teams, see
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
