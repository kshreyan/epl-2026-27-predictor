# Prediction Health Report

Generated: 2026-11-02T01:53:15.165960+00:00

**7 failures, 5 warnings, 23 informational** (out of 35 findings).

| Severity | Section | League | Finding |
|---|---|---|---|
| INFO | 1. Internal consistency | bundesliga | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | bundesliga | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): BUNDESLIGA2627_MW08_064_SVElversberg_1.FSVMainz05, BUNDESLIGA2627_MW08_065_FCSchalke04_RBLeipzig, BUNDESLIGA2627_MW08_066_SVWerderBremen_TSGHoffenheim, BUNDESLIGA2627_MW08_067_BorussiaMönchengladbach_SCPaderborn07, BUNDESLIGA2627_MW08_068_1.FCUnionBerlin_1.FCKöln ... |
| INFO | 3. Calibration / accuracy drift | bundesliga | 63 completed matches scored: accuracy=52.4%, multiclass Brier=0.598 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | bundesliga | 2 high-confidence (>=70%) miss(es): BUNDESLIGA2627_MW02_011_FCSchalke04_FCBayernMünchen (predicted away_win @77%, actual draw); BUNDESLIGA2627_MW05_041_FCAugsburg_FCBayernMünchen (predicted away_win @72%, actual draw) |
| INFO | 1. Internal consistency | epl | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | epl | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): EPL2627_MW09_084_Chelsea_ManchesterUnited, EPL2627_MW09_081_AFCBournemouth_LeedsUnited, EPL2627_MW09_083_Brentford_NottinghamForest, EPL2627_MW09_085_CoventryCity_Sunderland, EPL2627_MW09_086_HullCity_IpswichTown ... |
| INFO | 3. Calibration / accuracy drift | epl | 80 completed matches scored: accuracy=50.0%, multiclass Brier=0.608 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | epl | 1 high-confidence (>=70%) miss(es): EPL2627_MW05_049_NottinghamForest_CoventryCity (predicted home_win @82%, actual away_win) |
| INFO | 1. Internal consistency | la_liga | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | la_liga | 20 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LALIGA2627_MW08_076_MálagaCF_RCDEspanyoldeBarcelona, LALIGA2627_MW08_078_RayoVallecano_AthleticClub, LALIGA2627_MW08_071_DeportivoAlavés_AtléticodeMadrid, LALIGA2627_MW08_074_FCBarcelona_GetafeCF, LALIGA2627_MW08_079_RealMadrid_VillarrealCF ... |
| INFO | 3. Calibration / accuracy drift | la_liga | 90 completed matches scored: accuracy=54.4%, multiclass Brier=0.548 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ligue_1 | all 306 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | ligue_1 | 9 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): LIGUE12627_MW09_073_HavreAthleticClub_ParisSaint-Germain, LIGUE12627_MW09_074_LOSCLille_RCLens, LIGUE12627_MW09_078_OGCNice_StadeRennaisFC, LIGUE12627_MW09_075_FCLorient_StadeBrestois29, LIGUE12627_MW09_076_OlympiqueLyonnais_AngersSCO ... |
| INFO | 3. Calibration / accuracy drift | ligue_1 | 72 completed matches scored: accuracy=55.6%, multiclass Brier=0.584 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | nba | all 1200 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | nba | 3 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NBA2627_W02_401909903_OrlandoMagic_BostonCeltics, NBA2627_W02_401909904_IndianaPacers_BrooklynNets, NBA2627_W02_401909905_GoldenStateWarriors_LAClippers |
| INFO | 3. Calibration / accuracy drift | nba | 88 completed matches scored: accuracy=69.3%, multiclass Brier=0.369 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nba | 1 high-confidence (>=70%) miss(es): NBA2627_W01_401909876_DenverNuggets_GoldenStateWarriors (predicted home_win @74%, actual away_win) |
| INFO | 1. Internal consistency | ncaaf | all 761 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ncaaf | 500 completed matches scored: accuracy=70.0%, multiclass Brier=0.339 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | ncaaf | 15 high-confidence (>=70%) miss(es): NCAAF2627_W01_401856766_TCUHornedFrogs_NorthCarolinaTarHeels (predicted home_win @74%, actual away_win); NCAAF2627_W01_401858423_RutgersScarletKnights_MassachusettsMinutemen (predicted home_win @96%, actual away_win); NCAAF2627_W01_401856772_TulsaGoldenHurricane_OklahomaStateCowboys (predicted away_win @74%, actual home_win); NCAAF2627_W02_401858216_SyracuseOrange_CaliforniaGoldenBears (predicted home_win @74%, actual away_win); NCAAF2627_W02_401858444_UConnHuskies_MarylandTerrapins (predicted home_win @74%, actual away_win) ... |
| INFO | 1. Internal consistency | nfl | all 272 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | nfl | 12 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): NFL2627_W08_2026_08_BAL_BUF, NFL2627_W08_2026_08_TEN_CIN, NFL2627_W08_2026_08_ARI_DAL, NFL2627_W08_2026_08_MIN_DET, NFL2627_W08_2026_08_IND_JAX ... |
| INFO | 3. Calibration / accuracy drift | nfl | 108 completed matches scored: accuracy=69.4%, multiclass Brier=0.443 (lower is better, 0=perfect, 0.667=uniform guessing) |
| WARN | 3. Calibration / accuracy drift | nfl | 5 high-confidence (>=70%) miss(es): NFL2627_W01_2026_01_ARI_LAC (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_CAR_ATL (predicted home_win @75%, actual away_win); NFL2627_W02_2026_02_NO_BAL (predicted home_win @75%, actual away_win); NFL2627_W04_2026_04_NE_BUF (predicted home_win @75%, actual away_win); NFL2627_W06_2026_06_ARI_LA (predicted home_win @75%, actual away_win) |
| INFO | 1. Internal consistency | serie_a | all 380 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| FAIL | 2. Freshness & provenance | serie_a | 8 match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): SERIEA2627_MW10_092_Bologna_Monza, SERIEA2627_MW10_100_Udinese_Roma, SERIEA2627_MW10_098_Milan_Internazionale, SERIEA2627_MW10_093_Como_Venezia, SERIEA2627_MW10_094_Frosinone_Torino ... |
| INFO | 3. Calibration / accuracy drift | serie_a | 90 completed matches scored: accuracy=61.1%, multiclass Brier=0.523 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | ucl | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | ucl | 54 completed matches scored: accuracy=68.5%, multiclass Brier=0.496 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uecl | all 108 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uecl | 36 completed matches scored: accuracy=61.1%, multiclass Brier=0.581 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 1. Internal consistency | uel | all 144 rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence) |
| INFO | 3. Calibration / accuracy drift | uel | 54 completed matches scored: accuracy=55.6%, multiclass Brier=0.568 (lower is better, 0=perfect, 0.667=uniform guessing) |
| INFO | 4. Pipeline / site operational health | all | last 10 GitHub Actions runs all succeeded |
