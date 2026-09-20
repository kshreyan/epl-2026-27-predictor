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

export interface TrustedPickRow {
  rank: number
  league: string
  league_display_name: string
  match_id: string
  home_team: string
  away_team: string
  kickoff_utc: string
  matchweek: number
  status: string
  market: 'moneyline' | 'btts' | 'totals' | 'spread'
  pick: string
  probability: number
  edge: number
  outcome: 'win' | 'loss' | 'push' | null
  actual_score: string | null
}

export interface TrustedPicksWeek {
  week_start: string
  week_end: string
  picks: TrustedPickRow[]
}

export interface TrustedPicksPayload {
  generated_at: string
  model_version: string
  ranking_method: string
  weeks: TrustedPicksWeek[]
}

export interface NationsLeagueMatchRow {
  match_id: string
  season: string
  matchweek: number
  group: string
  date: string
  kickoff_utc: string
  home_team: string
  away_team: string
  stadium: string
  status: string
  actual_home_goals: number | null
  actual_away_goals: number | null
  actual_result: string | null
  home_win_prob: number
  draw_prob: number
  away_win_prob: number
  moneyline_pick: string
  home_elo: number
  away_elo: number
  predicted_score: string
  top_10_scorelines_json: ScorelineEntry[]
  btts_yes_prob: number
  btts_no_prob: number
  btts_pick: string
  total_goals_line: number
  over_prob: number
  under_prob: number
  totals_pick: string
  handicap_line: number
  home_cover_prob: number
  away_cover_prob: number
  spread_pick: string
  market_available: boolean
  market_home_odds: number | null
  market_draw_odds: number | null
  market_away_odds: number | null
  moneyline_model_source: string
  derived_markets_model_source: string
  run_id: string
  model_version: string
  generated_at: string
}

export interface NationsLeaguePredictionsPayload {
  league: string
  generated_at: string
  model_version: string
  season: string
  record_count: number
  moneyline_model_note?: string
  status?: string
  note?: string
  data: NationsLeagueMatchRow[]
}

export interface InternationalTrustedPickRow {
  rank: number
  match_id: string
  home_team: string
  away_team: string
  kickoff_utc: string
  matchweek: number
  group: string
  status: string
  market: 'moneyline'
  pick: string
  probability: number
  edge: number
  outcome: 'win' | 'loss' | 'push' | null
  actual_score: string | null
  market_available: boolean
}

export interface InternationalTrustedPicksWeek {
  week_start: string
  week_end: string
  picks: InternationalTrustedPickRow[]
}

export interface InternationalTrustedPicksPayload {
  generated_at: string
  model_version: string
  ranking_method: string
  status?: string
  note?: string
  weeks: InternationalTrustedPicksWeek[]
}
