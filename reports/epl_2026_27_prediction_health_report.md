# Prediction Health Report

Generated: 2026-10-27T00:31:52.548021+00:00

**5 failures, 2 warnings, 17 informational** (out of 24 findings).

| Severity | Section | League | Finding |
|---|---|---|---|
| INFO | 1. Internal consistency | bundesliga | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | bundesliga | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): BUNDESLIGA2627_MW07_055_SCPaderborn07_HamburgerSV, BUNDESLIGA2627_MW07_056_1.FCKöln_FCSchalke04, BUNDESLIGA2627_MW07_057_1.FSVMainz05_SVWerderBremen, BUNDESLIGA2627_MW07_058_FCAugsburg_1.FCUnionBerlin, BUNDESLIGA2627_MW07_059_Sport-ClubFreiburg_FCBayernMünchen ... |
| INFO | 3. Calibration / accuracy drift | bundesliga | 54 completed matches scored: accuracy=55.6%, multiclass Brier=0.592 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | bundesliga | 2 high-confidence (>=70%) miss(es): BUNDESLIGA2627_MW02_011_FCSchalke04_FCBayernMünchen (predicted away_win @77%, actual draw); BUNDESLIGA2627_MW05_041_FCAugsburg_FCBayernMünchen (predicted away_win @72%, actual draw) |
| INFO | 1. Internal consistency | epl | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | epl | 10 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): EPL2627_MW08_077_IpswichTown_NottinghamForest, EPL2627_MW08_072_AstonVilla_ManchesterCity, EPL2627_MW08_071_Arsenal_Everton, EPL2627_MW08_074_CoventryCity_Fulham, EPL2627_MW08_073_Chelsea_TottenhamHotspur ... |
| INFO | 3. Calibration / accuracy drift | epl | 70 completed matches scored: accuracy=51.4%, multiclass Brier=0.596 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | epl | 1 high-confidence (>=70%) miss(es): EPL2627_MW05_049_NottinghamForest_CoventryCity (predicted home_win @82%, actual away_win) |
| INFO | 1. Internal consistency | la_liga | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | la_liga | 20 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LALIGA2627_MW08_076_MálagaCF_RCDEspanyoldeBarcelona, LALIGA2627_MW08_078_RayoVallecano_AthleticClub, LALIGA2627_MW08_071_DeportivoAlavés_AtléticodeMadrid, LALIGA2627_MW08_074_FCBarcelona_GetafeCF, LALIGA2627_MW08_079_RealMadrid_VillarrealCF ... |
| INFO | 3. Calibration / accuracy drift | la_liga | 80 completed matches scored: accuracy=53.8%, multiclass Brier=0.543 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ligue_1 | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ligue_1 | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LIGUE12627_MW08_066_StadeBrestois29_OGCNice, LIGUE12627_MW08_072_ToulouseFC_EstacTroyes, LIGUE12627_MW08_067_RCLens_ParisFC, LIGUE12627_MW08_069_ASMonaco_LOSCLille, LIGUE12627_MW08_064_AngersSCO_FCLorient ... |
| INFO | 3. Calibration / accuracy drift | ligue_1 | 63 completed matches scored: accuracy=57.1%, multiclass Brier=0.582 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | serie_a | 10 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): SERIEA2627_MW08_079_Torino_Monza, SERIEA2627_MW08_072_Cagliari_Bologna, SERIEA2627_MW08_073_Como_Sassuolo, SERIEA2627_MW08_078_Napoli_Roma, SERIEA2627_MW08_076_Lazio_Parma ... |
| INFO | 3. Calibration / accuracy drift | serie_a | 70 completed matches scored: accuracy=58.6%, multiclass Brier=0.541 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 54 completed matches scored: accuracy=68.5%, multiclass Brier=0.496 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uecl | all 108 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uecl | 36 completed matches scored: accuracy=61.1%, multiclass Brier=0.581 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 54 completed matches scored: accuracy=55.6%, multiclass Brier=0.568 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
