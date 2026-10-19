# Prediction Health Report

Generated: 2026-10-19T21:03:58.706058+00:00

**5 failures, 2 warnings, 17 informational** (out of 24 findings).

| Severity | Section | League | Finding |
|---|---|---|---|
| INFO | 1. Internal consistency | bundesliga | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | bundesliga | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): BUNDESLIGA2627_MW06_046_SVElversberg_FCAugsburg, BUNDESLIGA2627_MW06_047_FCSchalke04_1.FSVMainz05, BUNDESLIGA2627_MW06_048_SVWerderBremen_SCPaderborn07, BUNDESLIGA2627_MW06_049_HamburgerSV_VfBStuttgart, BUNDESLIGA2627_MW06_050_BorussiaMönchengladbach_TSGHoffenheim ... |
| INFO | 3. Calibration / accuracy drift | bundesliga | 45 completed matches scored: accuracy=55.6%, multiclass Brier=0.595 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | bundesliga | 2 high-confidence (>=70%) miss(es): BUNDESLIGA2627_MW02_011_FCSchalke04_FCBayernMünchen (predicted away_win @77%, actual draw); BUNDESLIGA2627_MW05_041_FCAugsburg_FCBayernMünchen (predicted away_win @72%, actual draw) |
| INFO | 1. Internal consistency | epl | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | epl | 10 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): EPL2627_MW07_064_Everton_Chelsea, EPL2627_MW07_062_Brentford_Liverpool, EPL2627_MW07_065_Fulham_HullCity, EPL2627_MW07_067_ManchesterCity_IpswichTown, EPL2627_MW07_068_NewcastleUnited_AstonVilla ... |
| INFO | 3. Calibration / accuracy drift | epl | 60 completed matches scored: accuracy=48.3%, multiclass Brier=0.623 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | epl | 1 high-confidence (>=70%) miss(es): EPL2627_MW05_049_NottinghamForest_CoventryCity (predicted home_win @82%, actual away_win) |
| INFO | 1. Internal consistency | la_liga | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | la_liga | 20 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LALIGA2627_MW08_076_MálagaCF_RCDEspanyoldeBarcelona, LALIGA2627_MW08_078_RayoVallecano_AthleticClub, LALIGA2627_MW08_071_DeportivoAlavés_AtléticodeMadrid, LALIGA2627_MW08_074_FCBarcelona_GetafeCF, LALIGA2627_MW08_079_RealMadrid_VillarrealCF ... |
| INFO | 3. Calibration / accuracy drift | la_liga | 69 completed matches scored: accuracy=53.6%, multiclass Brier=0.542 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ligue_1 | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ligue_1 | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LIGUE12627_MW07_057_LeMansFC_ToulouseFC, LIGUE12627_MW07_062_RCStrasbourgAlsace_ParisSaint-Germain, LIGUE12627_MW07_058_LOSCLille_StadeBrestois29, LIGUE12627_MW07_063_EstacTroyes_RCLens, LIGUE12627_MW07_055_AngersSCO_OlympiquedeMarseille ... |
| INFO | 3. Calibration / accuracy drift | ligue_1 | 54 completed matches scored: accuracy=55.6%, multiclass Brier=0.596 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | serie_a | 10 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): SERIEA2627_MW07_063_Frosinone_Sassuolo, SERIEA2627_MW07_070_Venezia_Napoli, SERIEA2627_MW07_061_Bologna_Internazionale, SERIEA2627_MW07_068_Roma_Genoa, SERIEA2627_MW07_069_Udinese_Lecce ... |
| INFO | 3. Calibration / accuracy drift | serie_a | 60 completed matches scored: accuracy=60.0%, multiclass Brier=0.527 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 36 completed matches scored: accuracy=75.0%, multiclass Brier=0.480 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uecl | all 108 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uecl | 18 completed matches scored: accuracy=66.7%, multiclass Brier=0.537 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 36 completed matches scored: accuracy=58.3%, multiclass Brier=0.551 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
