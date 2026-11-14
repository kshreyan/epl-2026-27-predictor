# Prediction Health Report

Generated: 2026-11-14T10:38:39.938380+00:00

**3 failures, 6 warnings, 23 informational** (out of 32 findings).

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
| FAIL | 2. Freshness & provenance | nba | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NBA2627_W04_401909296_IndianaPacers_NewYorkKnicks, NBA2627_W04_401909297_OrlandoMagic_MilwaukeeBucks, NBA2627_W04_401909299_ChicagoBulls_AtlantaHawks, NBA2627_W04_401909298_MiamiHeat_ClevelandCavaliers, NBA2627_W04_401909300_NewOrleansPelicans_MemphisGrizzlies ... |
| INFO | 3. Calibration / accuracy drift | nba | 174 completed matches scored: accuracy=74.7%, multiclass Brier=0.335 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nba | 3 high-confidence (>=70%) miss(es): NBA2627_W02_401909895_PortlandTrailBlazers_MemphisGrizzlies (predicted home_win @77%, actual away_win); NBA2627_W02_401909911_OrlandoMagic_WashingtonWizards (predicted home_win @74%, actual away_win); NBA2627_W02_401909913_DallasMavericks_SacramentoKings (predicted home_win @74%, actual away_win) |
| INFO | 1. Internal consistency | ncaab | all 5414 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ncaab | 55 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NCAAB2627_W02_401921167_ClevelandStateVikings_WestFloridaArgonauts, NCAAB2627_W02_401909696_FloridaStateSeminoles_TexasA&M-CorpusChristiIslanders, NCAAB2627_W02_401921721_MiamiHurricanes_NorthAlabamaLions, NCAAB2627_W02_401923270_RutgersScarletKnights_BryantBulldogs, NCAAB2627_W02_401909515_ClemsonTigers_GeorgetownHoyas ... |
| INFO | 3. Calibration / accuracy drift | ncaab | 491 completed matches scored: accuracy=84.5%, multiclass Brier=0.224 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaab | 28 high-confidence (>=70%) miss(es): NCAAB2627_W01_401920982_VillanovaWildcats_NotreDameFightingIrish (predicted home_win @76%, actual away_win); NCAAB2627_W01_401909771_IowaStateCyclones_MemphisTigers (predicted home_win @89%, actual away_win); NCAAB2627_W01_401911261_St.BonaventureBonnies_YoungstownStatePenguins (predicted home_win @76%, actual away_win); NCAAB2627_W01_401920231_MaristRedFoxes_DartmouthBigGreen (predicted home_win @72%, actual away_win); NCAAB2627_W01_401910998_CoastalCarolinaChanticleers_EasternMichiganEagles (predicted home_win @76%, actual away_win) ... |
| INFO | 1. Internal consistency | ncaaf | all 761 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ncaaf | 3 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NCAAF2627_W11_401858293_PittsburghPanthers_FloridaStateSeminoles, NCAAF2627_W11_401858526_UCLABruins_IllinoisFightingIllini, NCAAF2627_W11_401856860_ColoradoBuffaloes_HoustonCougars |
| INFO | 3. Calibration / accuracy drift | ncaaf | 570 completed matches scored: accuracy=68.9%, multiclass Brier=0.348 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaaf | 15 high-confidence (>=70%) miss(es): NCAAF2627_W01_401858423_RutgersScarletKnights_MassachusettsMinutemen (predicted home_win @92%, actual away_win); NCAAF2627_W01_401856772_TulsaGoldenHurricane_OklahomaStateCowboys (predicted away_win @74%, actual home_win); NCAAF2627_W02_401864571_EastCarolinaPirates_AppStateMountaineers (predicted home_win @74%, actual away_win); NCAAF2627_W02_401860884_TexasStateBobcats_UTSARoadrunners (predicted home_win @74%, actual away_win); NCAAF2627_W03_401856691_SouthCarolinaGamecocks_MississippiStateBulldogs (predicted home_win @80%, actual away_win) ... |
| INFO | 1. Internal consistency | nfl | all 272 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | nfl | 137 completed matches scored: accuracy=72.3%, multiclass Brier=0.428 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nfl | 7 high-confidence (>=70%) miss(es): NFL2627_W01_2026_01_ARI_LAC (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_CAR_ATL (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_NO_BAL (predicted home_win @75%, actual away_win); NFL2627_W03_2026_03_ATL_GB (predicted home_win @75%, actual away_win); NFL2627_W04_2026_04_NE_BUF (predicted home_win @75%, actual away_win) ... |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | serie_a | 110 completed matches scored: accuracy=61.8%, multiclass Brier=0.523 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 72 completed matches scored: accuracy=73.6%, multiclass Brier=0.486 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 72 completed matches scored: accuracy=51.4%, multiclass Brier=0.587 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
