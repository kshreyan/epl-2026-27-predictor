# Prediction Health Report

Generated: 2026-11-10T04:10:50.057161+00:00

**3 failures, 6 warnings, 27 informational** (out of 36 findings).

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
| INFO | 3. Calibration / accuracy drift | ligue_1 | 91 completed matches scored: accuracy=56.0%, multiclass Brier=0.574 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nations_league | all 156 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | nations_league | 104 completed matches scored: accuracy=54.8%, multiclass Brier=0.593 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nba | all 1200 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | nba | 8 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NBA2627_W03_401909952_AtlantaHawks_LosAngelesLakers, NBA2627_W03_401909953_CharlotteHornets_ClevelandCavaliers, NBA2627_W03_401909954_DetroitPistons_WashingtonWizards, NBA2627_W03_401909955_TorontoRaptors_MemphisGrizzlies, NBA2627_W03_401909956_DallasMavericks_IndianaPacers ... |
| INFO | 3. Calibration / accuracy drift | nba | 146 completed matches scored: accuracy=74.0%, multiclass Brier=0.347 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nba | 4 high-confidence (>=70%) miss(es): NBA2627_W01_401909850_GoldenStateWarriors_MemphisGrizzlies (predicted home_win @74%, actual away_win); NBA2627_W01_401909863_NewYorkKnicks_OrlandoMagic (predicted home_win @74%, actual away_win); NBA2627_W02_401909895_PortlandTrailBlazers_MemphisGrizzlies (predicted home_win @74%, actual away_win); NBA2627_W02_401909913_DallasMavericks_SacramentoKings (predicted home_win @74%, actual away_win) |
| INFO | 1. Internal consistency | ncaab | all 5413 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ncaab | 33 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NCAAB2627_W02_401916315_OhioStateBuckeyes_MarshallThunderingHerd, NCAAB2627_W02_401909718_IndianaHoosiers_SyracuseOrange, NCAAB2627_W02_401921180_PennsylvaniaQuakers_HowardBison, NCAAB2627_W02_401918074_ClemsonTigers_NorthDakotaFightingHawks, NCAAB2627_W02_401925681_NotreDameFightingIrish_EasternIllinoisPanthers ... |
| INFO | 3. Calibration / accuracy drift | ncaab | 329 completed matches scored: accuracy=84.8%, multiclass Brier=0.228 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaab | 23 high-confidence (>=70%) miss(es): NCAAB2627_W01_401920982_VillanovaWildcats_NotreDameFightingIrish (predicted home_win @80%, actual away_win); NCAAB2627_W01_401911304_BrownBears_NewHampshireWildcats (predicted home_win @72%, actual away_win); NCAAB2627_W01_401909771_IowaStateCyclones_MemphisTigers (predicted home_win @87%, actual away_win); NCAAB2627_W01_401911261_St.BonaventureBonnies_YoungstownStatePenguins (predicted home_win @72%, actual away_win); NCAAB2627_W01_401920231_MaristRedFoxes_DartmouthBigGreen (predicted home_win @74%, actual away_win) ... |
| INFO | 1. Internal consistency | ncaaf | all 761 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ncaaf | 562 completed matches scored: accuracy=68.7%, multiclass Brier=0.351 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaaf | 16 high-confidence (>=70%) miss(es): NCAAF2627_W01_401858423_RutgersScarletKnights_MassachusettsMinutemen (predicted home_win @91%, actual away_win); NCAAF2627_W01_401856772_TulsaGoldenHurricane_OklahomaStateCowboys (predicted away_win @74%, actual home_win); NCAAF2627_W02_401864571_EastCarolinaPirates_AppStateMountaineers (predicted home_win @74%, actual away_win); NCAAF2627_W02_401860884_TexasStateBobcats_UTSARoadrunners (predicted home_win @74%, actual away_win); NCAAF2627_W03_401856691_SouthCarolinaGamecocks_MississippiStateBulldogs (predicted home_win @80%, actual away_win) ... |
| INFO | 1. Internal consistency | nfl | all 272 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | nfl | 1 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NFL2627_W09_2026_09_BUF_MIN |
| INFO | 3. Calibration / accuracy drift | nfl | 135 completed matches scored: accuracy=71.9%, multiclass Brier=0.435 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nfl | 9 high-confidence (>=70%) miss(es): NFL2627_W01_2026_01_ARI_LAC (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_CAR_ATL (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_NO_BAL (predicted home_win @75%, actual away_win); NFL2627_W03_2026_03_ATL_GB (predicted home_win @75%, actual away_win); NFL2627_W04_2026_04_NE_BUF (predicted home_win @75%, actual away_win) ... |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | serie_a | 110 completed matches scored: accuracy=61.8%, multiclass Brier=0.523 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 72 completed matches scored: accuracy=70.8%, multiclass Brier=0.489 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uecl | all 108 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uecl | 54 completed matches scored: accuracy=63.0%, multiclass Brier=0.570 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 72 completed matches scored: accuracy=51.4%, multiclass Brier=0.578 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
