# Prediction Health Report

Generated: 2026-11-19T09:24:30.308377+00:00

**1 failures, 7 warnings, 23 informational** (out of 31 findings).

| Severity | Section | League | Finding |
|---|---|---|---|
| INFO | 1. Internal consistency | bundesliga | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | bundesliga | 81 completed matches scored: accuracy=54.3%, multiclass Brier=0.582 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | bundesliga | 2 high-confidence (>=70%) miss(es): BUNDESLIGA2627_MW02_011_FCSchalke04_FCBayernMünchen (predicted away_win @77%, actual draw); BUNDESLIGA2627_MW05_041_FCAugsburg_FCBayernMünchen (predicted away_win @72%, actual draw) |
| INFO | 1. Internal consistency | epl | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | epl | 100 completed matches scored: accuracy=51.0%, multiclass Brier=0.604 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | epl | 1 high-confidence (>=70%) miss(es): EPL2627_MW05_049_NottinghamForest_CoventryCity (predicted home_win @82%, actual away_win) |
| INFO | 1. Internal consistency | la_liga | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | la_liga | 119 completed matches scored: accuracy=55.5%, multiclass Brier=0.538 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ligue_1 | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ligue_1 | 90 completed matches scored: accuracy=56.7%, multiclass Brier=0.569 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nba | all 1200 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | nba | 222 completed matches scored: accuracy=71.6%, multiclass Brier=0.361 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nba | 9 high-confidence (>=70%) miss(es): NBA2627_W01_401909876_DenverNuggets_GoldenStateWarriors (predicted home_win @74%, actual away_win); NBA2627_W02_401909888_MinnesotaTimberwolves_GoldenStateWarriors (predicted home_win @74%, actual away_win); NBA2627_W02_401909911_OrlandoMagic_WashingtonWizards (predicted home_win @74%, actual away_win); NBA2627_W02_401909913_DallasMavericks_SacramentoKings (predicted home_win @77%, actual away_win); NBA2627_W03_401909927_MemphisGrizzlies_IndianaPacers (predicted home_win @74%, actual away_win) ... |
| INFO | 1. Internal consistency | ncaab | all 5424 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ncaab | 4 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NCAAB2627_W02_401924720_CornellBigRed_UNCGreensboroSpartans, NCAAB2627_W02_401917529_PacificTigers_AirForceFalcons, NCAAB2627_W02_401926864_UNCWilmingtonSeahawks_LouisianaRagin'Cajuns, NCAAB2627_W02_401926073_OregonDucks_PepperdineWaves |
| INFO | 3. Calibration / accuracy drift | ncaab | 776 completed matches scored: accuracy=82.2%, multiclass Brier=0.241 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaab | 47 high-confidence (>=70%) miss(es): NCAAB2627_W01_401920982_VillanovaWildcats_NotreDameFightingIrish (predicted home_win @72%, actual away_win); NCAAB2627_W01_401909771_IowaStateCyclones_MemphisTigers (predicted home_win @87%, actual away_win); NCAAB2627_W01_401911261_St.BonaventureBonnies_YoungstownStatePenguins (predicted home_win @80%, actual away_win); NCAAB2627_W01_401921139_ColumbiaLions_ElonPhoenix (predicted home_win @76%, actual away_win); NCAAB2627_W01_401920231_MaristRedFoxes_DartmouthBigGreen (predicted home_win @73%, actual away_win) ... |
| INFO | 1. Internal consistency | ncaaf | all 761 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ncaaf | 634 completed matches scored: accuracy=66.7%, multiclass Brier=0.364 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaaf | 19 high-confidence (>=70%) miss(es): NCAAF2627_W01_401858423_RutgersScarletKnights_MassachusettsMinutemen (predicted home_win @91%, actual away_win); NCAAF2627_W02_401858217_IllinoisFightingIllini_DukeBlueDevils (predicted home_win @74%, actual away_win); NCAAF2627_W02_401858216_SyracuseOrange_CaliforniaGoldenBears (predicted home_win @74%, actual away_win); NCAAF2627_W03_401856691_SouthCarolinaGamecocks_MississippiStateBulldogs (predicted home_win @74%, actual away_win); NCAAF2627_W03_401858232_MarylandTerrapins_VirginiaTechHokies (predicted home_win @80%, actual away_win) ... |
| INFO | 1. Internal consistency | nfl | all 272 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | nfl | 150 completed matches scored: accuracy=71.3%, multiclass Brier=0.426 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nfl | 7 high-confidence (>=70%) miss(es): NFL2627_W01_2026_01_ARI_LAC (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_NO_BAL (predicted home_win @75%, actual away_win); NFL2627_W03_2026_03_ATL_GB (predicted home_win @75%, actual away_win); NFL2627_W04_2026_04_NE_BUF (predicted home_win @75%, actual away_win); NFL2627_W06_2026_06_ARI_LA (predicted home_win @75%, actual away_win) ... |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | serie_a | 110 completed matches scored: accuracy=61.8%, multiclass Brier=0.523 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 72 completed matches scored: accuracy=77.8%, multiclass Brier=0.374 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ucl | 3 high-confidence (>=70%) miss(es): UCL2627_MW02_100_Feyenoord_Como (predicted away_win @74%, actual home_win); UCL2627_MW03_123_SportingCP_LASK (predicted home_win @73%, actual away_win); UCL2627_MW04_136_Fenerbahce_Liverpool (predicted away_win @73%, actual home_win) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 72 completed matches scored: accuracy=52.8%, multiclass Brier=0.572 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
