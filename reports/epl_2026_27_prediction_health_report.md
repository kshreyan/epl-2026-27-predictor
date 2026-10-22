# Prediction Health Report

Generated: 2026-10-22T00:41:31.087718+00:00

**3 failures, 2 warnings, 21 informational** (out of 26 findings).

| Severity | Section | League | Finding |
|---|---|---|---|
| INFO | 1. Internal consistency | bundesliga | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | bundesliga | 54 completed matches scored: accuracy=55.6%, multiclass Brier=0.592 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | bundesliga | 2 high-confidence (>=70%) miss(es): BUNDESLIGA2627_MW02_011_FCSchalke04_FCBayernMünchen (predicted away_win @77%, actual draw); BUNDESLIGA2627_MW05_041_FCAugsburg_FCBayernMünchen (predicted away_win @72%, actual draw) |
| INFO | 1. Internal consistency | epl | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | epl | 70 completed matches scored: accuracy=51.4%, multiclass Brier=0.596 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | epl | 1 high-confidence (>=70%) miss(es): EPL2627_MW05_049_NottinghamForest_CoventryCity (predicted home_win @82%, actual away_win) |
| INFO | 1. Internal consistency | la_liga | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | la_liga | 11 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LALIGA2627_MW06_057_LevanteUD_AthleticClub, LALIGA2627_MW08_076_MálagaCF_RCDEspanyoldeBarcelona, LALIGA2627_MW08_078_RayoVallecano_AthleticClub, LALIGA2627_MW08_071_DeportivoAlavés_AtléticodeMadrid, LALIGA2627_MW08_074_FCBarcelona_GetafeCF ... |
| INFO | 3. Calibration / accuracy drift | la_liga | 79 completed matches scored: accuracy=54.4%, multiclass Brier=0.540 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ligue_1 | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ligue_1 | 63 completed matches scored: accuracy=57.1%, multiclass Brier=0.582 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nba | all 1200 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | nba | 8 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NBA2627_W01_401909834_OrlandoMagic_AtlantaHawks, NBA2627_W01_401909835_WashingtonWizards_MilwaukeeBucks, NBA2627_W01_401909836_BrooklynNets_CharlotteHornets, NBA2627_W01_401909837_TorontoRaptors_ChicagoBulls, NBA2627_W01_401909091_MiamiHeat_MinnesotaTimberwolves ... |
| INFO | 3. Calibration / accuracy drift | nba | 3 completed matches scored: accuracy=66.7%, multiclass Brier=0.488 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nfl | all 272 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | nfl | 93 completed matches scored: accuracy=50.5%, multiclass Brier=0.507 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | serie_a | 70 completed matches scored: accuracy=58.6%, multiclass Brier=0.541 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ucl | 18 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): UCL2627_MW03_109_Fenerbahce_SlaviaPraha, UCL2627_MW03_110_SabahFK_BorussiaDortmund, UCL2627_MW03_111_ParisSaint-Germain_Barcelona, UCL2627_MW03_112_Liverpool_Villarreal, UCL2627_MW03_113_ManchesterCity_AEKAthens ... |
| INFO | 3. Calibration / accuracy drift | ucl | 36 completed matches scored: accuracy=75.0%, multiclass Brier=0.481 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uecl | all 108 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uecl | 18 completed matches scored: accuracy=66.7%, multiclass Brier=0.537 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 36 completed matches scored: accuracy=58.3%, multiclass Brier=0.551 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
