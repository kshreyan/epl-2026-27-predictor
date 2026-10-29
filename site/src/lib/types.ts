// Mirrors the real JSON schemas in data/outputs/dashboard/*.json exactly
// (field names, nullability) -- verified against the actual committed
// files, not guessed from the pipeline's Python source.

export interface Envelope<T> {
  generated_at: string
  model_version: string
  season: string
  record_count: number
  data: T[]
}

export interface KnockoutProbabilityRow {
  n_trials: number
  team: string
  current_elo: number
  current_points: number
  current_goal_diff: number
  prob_direct_round_of_16: number
  prob_playoff_round_zone: number
  prob_eliminated_league_phase: number
  prob_reach_round_of_16: number
  prob_reach_quarter_final: number
  prob_reach_semi_final: number
  prob_reach_final: number
  prob_win_competition: number
  generated_at: string
  model_version: string
}

export interface KnockoutProbabilityPayload extends Envelope<KnockoutProbabilityRow> {
  status?: string
  note?: string
  n_trials?: number | null
}

// NFL has prob_seed_1..7 + prob_win_division; NBA has prob_seed_1..8,
// no prob_win_division (no real division-winner concept drives NBA
// seeding) -- a flexible index, same convention PositionDistributionRow
// already uses for a similarly per-league-shaped row, read with the
// getSeedProbability helper in lib/format.ts rather than a precise
// (and awkward-in-TS) type.
export type PlayoffPictureRow = {
  team: string
  conference: string
  division: string
  current_win_pct: number | null
  current_point_diff: number
  prob_make_playoffs: number
  prob_direct_seed: number
} & Record<string, string | number | null>

export interface PlayoffPicturePayload extends Envelope<PlayoffPictureRow> {
  status?: string
  note?: string
  n_trials?: number | null
}

// NCAA Football's real shape (simulate_team_sport_season.py's
// main_ncaaf_bowl_eligibility()) is genuinely different from the
// seeded-playoff shape above -- no real seeding formula exists for
// this sport (the real CFP is committee-selected), so this reports
// conference win-loss projection and real bowl eligibility instead.
// Served from the same `${leagueId}_playoff_picture.json` endpoint --
// StandingsPage picks the right row shape to render by checking for
// `prob_bowl_eligible`.
export type BowlEligibilityRow = {
  team: string
  conference: string
  current_wins: number
  current_games: number
  current_conference_win_pct: number | null
  mean_projected_final_wins: number
  prob_bowl_eligible: number
  prob_best_conference_record: number
} & Record<string, string | number | null>

export interface ExpectedTableRow {
  team: string
  expected_position: number
  median_position: number
  position_5th_percentile: number
  position_25th_percentile: number
  position_75th_percentile: number
  position_95th_percentile: number
  expected_points: number
  points_5th_percentile: number
  points_25th_percentile: number
  median_points: number
  points_75th_percentile: number
  points_95th_percentile: number
  expected_wins: number
  expected_draws: number
  expected_losses: number
  expected_goals_for: number
  expected_goals_against: number
  expected_goal_difference: number
  title_probability: number
  top_4_probability: number
  top_5_probability: number
  top_half_probability: number
  relegation_probability: number
  most_likely_finish: number
  model_version: string
  generated_at: string
}

export interface RaceRow {
  team: string
  title_probability?: number
  top_4_probability?: number
  relegation_probability?: number
  expected_points: number
  expected_position?: number
  median_points?: number
}

export interface ScorelineEntry {
  score: string
  probability: number
}

export interface MatchPredictionRow {
  match_id: string
  season: string
  matchweek: number
  date: string
  kickoff_utc: string
  home_team: string
  away_team: string
  stadium: string
  status: string
  prediction_mode: string
  actual_home_goals: number | null
  actual_away_goals: number | null
  actual_result: string | null
  home_expected_goals_model_only: number
  away_expected_goals_model_only: number
  home_expected_goals_market_integrated: number | null
  away_expected_goals_market_integrated: number | null
  predicted_score_model_only: string
  predicted_score_market_integrated: string | null
  predicted_result_model_only: string
  predicted_result_market_integrated: string | null
  home_win_prob_model_only: number
  draw_prob_model_only: number
  away_win_prob_model_only: number
  home_win_prob_market_integrated: number | null
  draw_prob_market_integrated: number | null
  away_win_prob_market_integrated: number | null
  moneyline_pick: string
  btts_pick: string
  totals_pick: string
  spread_pick: string
  top_10_scorelines_model_only_json: ScorelineEntry[]
  top_10_scorelines_market_integrated_json: ScorelineEntry[] | null
  market_available: boolean
  closing_market_available: boolean
  market_blend_applied: boolean
  btts_yes_prob_model_only: number
  btts_no_prob_model_only: number
  total_goals_line_model_only: number
  over_prob_model_only: number
  under_prob_model_only: number
  totals_blend_applied: boolean
  handicap_line_model_only: number
  home_cover_prob_model_only: number
  away_cover_prob_model_only: number
  handicap_blend_applied: boolean
  squad_data_available: boolean
  injury_data_available: boolean
  lineup_data_available: boolean
  rest_day_diff: number | null
  congestion_diff: number | null
  confidence: number
  upset_risk: number
  data_quality_score: number
  run_id: string
  model_version: string
  generated_at: string
}

// `team` is a string, finish_1_probability..finish_20_probability are
// numbers -- a mixed-value record, read with the getFinishProbability
// helper in lib/format.ts rather than a precise (and awkward-in-TS) type.
export type PositionDistributionRow = Record<string, string | number>

export interface ModelComparisonRow {
  model: string
  n_matches: number
  log_loss: number
  brier_score: number
  ranked_probability_score: number
  accuracy: number
  favorite_accuracy: number
  draw_calibration_bias: number
  expected_calibration_error: number | null
}

export interface ReliabilityBin {
  outcome_class: 'home_win' | 'draw' | 'away_win'
  bin_lower: number
  bin_upper: number
  n_matches: number
  mean_predicted_probability: number | null
  empirical_frequency: number | null
}

export interface CalibrationSummary {
  method: string
  ece: number
  raw_log_loss: number
  calibrated_log_loss: number
  n_matches: number
  generated_at: string
}

export interface EnsembleSeasonRow {
  season: string
  n_matches: number
  dc_log_loss: number
  ensemble_log_loss: number
  ensemble_wins_season: boolean
}

export interface ModelPerformancePayload extends Envelope<ModelComparisonRow> {
  reliability_table: ReliabilityBin[]
  calibration_summary: CalibrationSummary | null
  ensemble_per_season_comparison: EnsembleSeasonRow[]
}

export interface MarginSurvivalRow {
  match_id: string
  league_id: string
  season: string
  matchweek: number
  date: string
  kickoff_utc: string
  status: string
  team: string
  opponent: string
  is_home: boolean
  predicted_score_model_only: string
  eligible: boolean
  win_prob: number
  draw_prob: number
  lose_1_prob: number
  lose_2_prob: number
  lose_3_prob: number
  lose_4plus_prob: number
  p_cover: number
  p_push: number
  p_fail: number
  p_survive: number
  risk_label: string
  factor_strength_gap_score: number | null
  factor_low_total_score: number | null
  factor_historical_tail_score: number | null
  factor_opponent_blowout_score: number | null
  factor_rotation_score: number | null
  team_history_n_matches: number
  team_history_loss3plus_rate: number | null
  opponent_history_n_matches: number
  opponent_history_win3plus_rate: number | null
  real_line: number | null
  real_odds: number | null
  real_bookmaker: string | null
  cover_prob_at_real_line: number | null
  implied_prob_at_real_line: number | null
  value_gap: number | null
  fair_plus2_decimal_odds: number | null
  // This league's own real blowout line (2 goals for soccer/UEFA, 14
  // points for NFL, 20 points for NBA -- see
  // compute_margin_survival.py's THRESHOLD / compute_margin_survival_
  // team_sport.py's MARGIN_THRESHOLD). `verdict` is formatted from this
  // same real number, never a borrowed "+2".
  threshold: number
  verdict: `PICK +${number}` | `LEAN +${number}` | 'PASS'
  why_text: string
  data_confidence?: 'high' | 'moderate' | 'low'
  league_display_name?: string
  rank?: number
  // True only on the favored team's own row, checked across every real
  // upcoming fixture (not just the next round/slate): a real ELITE
  // SURVIVAL PICK verdict, a HIGH BLOWOUT RISK opponent, a better own
  // predicted scoreline, AND a real top-third-vs-bottom-half gap in
  // the current real standings, all at once -- see
  // build_margin_survival_json.py's _flag_pick_moneyline().
  pick_moneyline?: boolean
  run_id: string
  model_version: string
  generated_at: string
}

export interface MarginSurvivalPayload extends Envelope<MarginSurvivalRow> {
  engine_note?: string
  status?: string
  note?: string
  verdict_tally?: Record<string, number>
  pick_moneyline_count?: number
}

export interface Top20MarginSurvivalPayload {
  generated_at: string
  model_version: string
  season: string
  view: string
  note?: string
  record_count: number
  data: MarginSurvivalRow[]
}

export interface PickMoneylinePayload {
  generated_at: string
  model_version: string
  season: string
  note?: string
  record_count: number
  data: MarginSurvivalRow[]
}

