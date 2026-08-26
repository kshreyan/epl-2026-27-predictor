import { useMemo, useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type { Envelope, MatchPredictionRow } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { DataQualityBadge } from '../components/DataQualityBadge'
import { ScorelineDistribution } from '../components/ScorelineDistribution'
import { PageState } from '../components/PageState'

function ProbBar({ home, draw, away }: { home: number; draw: number; away: number }) {
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-sm">
      <div style={{ width: `${home * 100}%` }} className="bg-[var(--color-accent)]" title={`Home ${pct(home)}`} />
      <div style={{ width: `${draw * 100}%` }} className="bg-[var(--color-text-faint)]" title={`Draw ${pct(draw)}`} />
      <div style={{ width: `${away * 100}%` }} className="bg-[var(--color-positive)]" title={`Away ${pct(away)}`} />
    </div>
  )
}

function MatchRow({ match }: { match: MatchPredictionRow }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="grid w-full grid-cols-[100px_1fr_80px_140px_auto] items-center gap-3 px-2 py-2 text-left hover:bg-[var(--color-panel)]"
      >
        <span className="tnum text-[11px] text-[var(--color-text-faint)]">{formatKickoff(match.kickoff_utc)}</span>
        <span className="text-[12px]">
          {match.home_team} <span className="text-[var(--color-text-faint)]">v</span> {match.away_team}
        </span>
        <span className="tnum text-center text-[13px] font-medium text-[var(--color-accent)]">
          {match.predicted_score_model_only}
        </span>
        <ProbBar home={match.home_win_prob_model_only} draw={match.draw_prob_model_only} away={match.away_win_prob_model_only} />
        <DataQualityBadge marketAvailable={match.market_available} dataQualityScore={match.data_quality_score} />
      </button>
      {open && (
        <div className="grid grid-cols-1 gap-4 border-t border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-3 md:grid-cols-2">
          <div>
            <h3 className="mb-1 text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Top-10 scorelines (model-only)</h3>
            <ScorelineDistribution scorelines={match.top_10_scorelines_model_only_json} />
          </div>
          <div className="space-y-2 text-[11px]">
            <h3 className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Model vs. market</h3>
            <div className="tnum grid grid-cols-3 gap-2">
              <div>
                <div className="text-[var(--color-text-faint)]">Home</div>
                <div>{pct(match.home_win_prob_model_only)}</div>
              </div>
              <div>
                <div className="text-[var(--color-text-faint)]">Draw</div>
                <div>{pct(match.draw_prob_model_only)}</div>
              </div>
              <div>
                <div className="text-[var(--color-text-faint)]">Away</div>
                <div>{pct(match.away_win_prob_model_only)}</div>
              </div>
            </div>
            <p className="text-[var(--color-text-faint)]">
              {match.market_blend_applied
                ? 'Real market odds blended in (validated model+market blend).'
                : match.market_available
                  ? 'Market-integrated probabilities available.'
                  : 'No market data available -- no live odds feed is configured (model-only prediction).'}
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                injury data: {match.injury_data_available ? 'available' : 'unavailable'}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                lineup data: {match.lineup_data_available ? 'available' : 'unavailable'}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                confidence: {pct(match.confidence)}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                upset risk: {pct(match.upset_risk)}
              </span>
            </div>
          </div>
          <div className="space-y-2 text-[11px] md:col-span-2">
            <h3 className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Other markets</h3>
            <div className="tnum grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="border border-[var(--color-border)] p-2">
                <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                  <span>Both teams to score</span>
                  <span title="No real market source exists for BTTS on this sport (checked directly) -- always model-only.">model-only</span>
                </div>
                <div className="flex justify-between"><span>Yes</span><span>{pct(match.btts_yes_prob_model_only)}</span></div>
                <div className="flex justify-between"><span>No</span><span>{pct(match.btts_no_prob_model_only)}</span></div>
              </div>
              <div className="border border-[var(--color-border)] p-2">
                <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                  <span>Spread (line {match.handicap_line_model_only > 0 ? '+' : ''}{match.handicap_line_model_only})</span>
                  <span>{match.handicap_blend_applied ? 'market-blended' : 'model-only'}</span>
                </div>
                <div className="flex justify-between"><span>Home covers</span><span>{pct(match.home_cover_prob_model_only)}</span></div>
                <div className="flex justify-between"><span>Away covers</span><span>{pct(match.away_cover_prob_model_only)}</span></div>
              </div>
              <div className="border border-[var(--color-border)] p-2">
                <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                  <span>Totals (line {match.total_goals_line_model_only})</span>
                  <span>{match.totals_blend_applied ? 'market-blended' : 'model-only'}</span>
                </div>
                <div className="flex justify-between"><span>Over</span><span>{pct(match.over_prob_model_only)}</span></div>
                <div className="flex justify-between"><span>Under</span><span>{pct(match.under_prob_model_only)}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export function FixturesPage() {
  const { data, error, loading } = useDashboardJson<Envelope<MatchPredictionRow>>('epl_match_predictions.json')
  const [pickedMatchweek, setPickedMatchweek] = useState<number | null>(null)

  const matchweeks = useMemo(
    () => (data ? [...new Set(data.data.map((m) => m.matchweek))].sort((a, b) => a - b) : []),
    [data],
  )

  // Default to the first matchweek that isn't fully completed (rather
  // than always matchweek 1), so the page shows upcoming fixtures --
  // with real, current model+market predictions -- once the season is
  // underway, instead of an already-played week whose rows are frozen
  // at their original pre-kickoff values.
  const defaultMatchweek = useMemo(() => {
    if (!data) return 1
    return matchweeks.find((mw) => data.data.some((m) => m.matchweek === mw && m.status !== 'completed')) ?? matchweeks[0] ?? 1
  }, [data, matchweeks])
  const matchweek = pickedMatchweek ?? defaultMatchweek

  const matches = useMemo(
    () => (data ? data.data.filter((m) => m.matchweek === matchweek).sort((a, b) => a.kickoff_utc.localeCompare(b.kickoff_utc)) : []),
    [data, matchweek],
  )

  if (loading || error || !data) return <PageState loading={loading} error={error} />

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="flex items-center gap-2">
        <label htmlFor="mw" className="text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">
          Matchweek
        </label>
        <select
          id="mw"
          value={matchweek}
          onChange={(e) => setPickedMatchweek(Number(e.target.value))}
          className="tnum border border-[var(--color-border)] bg-[var(--color-panel)] px-2 py-1 text-[12px]"
        >
          {matchweeks.map((mw) => (
            <option key={mw} value={mw}>
              MW {mw}
            </option>
          ))}
        </select>
      </div>
      <div className="border border-[var(--color-border)]">
        {matches.map((m) => (
          <MatchRow key={m.match_id} match={m} />
        ))}
      </div>
    </div>
  )
}
