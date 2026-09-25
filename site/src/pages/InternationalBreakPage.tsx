import { useMemo, useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type { NationsLeagueMatchRow, NationsLeaguePredictionsPayload } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { FinalScore } from '../components/FinalScore'
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

function MatchRow({ match }: { match: NationsLeagueMatchRow }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="grid w-full grid-cols-[100px_90px_1fr_80px_140px] items-center gap-3 px-2 py-2 text-left hover:bg-[var(--color-panel)]"
      >
        <span className="tnum text-[11px] text-[var(--color-text-faint)]">{formatKickoff(match.kickoff_utc)}</span>
        <span className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{match.group}</span>
        <span className="text-[12px]">
          {match.home_team} <span className="text-[var(--color-text-faint)]">v</span> {match.away_team}
        </span>
        <span className="text-center">
          <span className="tnum block text-[13px] font-medium text-[var(--color-accent)]">{match.predicted_score}</span>
          <FinalScore
            status={match.status}
            actualHomeGoals={match.actual_home_goals}
            actualAwayGoals={match.actual_away_goals}
          />
        </span>
        <ProbBar home={match.home_win_prob} draw={match.draw_prob} away={match.away_win_prob} />
      </button>
      {open && (
        <div className="space-y-2 border-t border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-3 text-[11px]">
          <div className="tnum grid grid-cols-3 gap-2">
            <div><div className="text-[var(--color-text-faint)]">Home ({match.home_elo.toFixed(0)} Elo)</div><div>{pct(match.home_win_prob)}</div></div>
            <div><div className="text-[var(--color-text-faint)]">Draw</div><div>{pct(match.draw_prob)}</div></div>
            <div><div className="text-[var(--color-text-faint)]">Away ({match.away_elo.toFixed(0)} Elo)</div><div>{pct(match.away_win_prob)}</div></div>
          </div>
          <p className="text-[var(--color-text-faint)]">{match.moneyline_model_source}</p>
          {match.market_available && (
            <p className="tnum text-[var(--color-text-faint)]">
              Real current market odds: {match.market_home_odds} / {match.market_draw_odds} / {match.market_away_odds}
            </p>
          )}
          <div className="flex flex-wrap gap-1.5 pt-1">
            <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px]">
              <span className="text-[var(--color-text-faint)]">BTTS: </span>
              <span className="font-medium text-[var(--color-accent)]">{match.btts_pick}</span>
            </span>
            <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px]">
              <span className="text-[var(--color-text-faint)]">Totals: </span>
              <span className="font-medium text-[var(--color-accent)]">{match.totals_pick}</span>
            </span>
            <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px]">
              <span className="text-[var(--color-text-faint)]">Spread: </span>
              <span className="font-medium text-[var(--color-accent)]">{match.spread_pick}</span>
            </span>
          </div>
          <p className="text-[var(--color-text-faint)]">{match.derived_markets_model_source}</p>
        </div>
      )}
    </div>
  )
}

export function InternationalBreakPage() {
  const { data: predictions, error: predError, loading: predLoading } =
    useDashboardJson<NationsLeaguePredictionsPayload>('nations_league_match_predictions.json')
  const [pickedMatchday, setPickedMatchday] = useState<number | null>(null)

  const matchdays = useMemo(
    () => (predictions ? [...new Set(predictions.data.map((m) => m.matchweek))].sort((a, b) => a - b) : []),
    [predictions],
  )
  const defaultMatchday = useMemo(() => {
    if (!predictions) return 1
    return matchdays.find((md) => predictions.data.some((m) => m.matchweek === md && m.status !== 'completed')) ?? matchdays[0] ?? 1
  }, [predictions, matchdays])
  const matchday = pickedMatchday ?? defaultMatchday

  const matches = useMemo(
    () => (predictions ? predictions.data.filter((m) => m.matchweek === matchday).sort((a, b) => a.kickoff_utc.localeCompare(b.kickoff_utc)) : []),
    [predictions, matchday],
  )

  if (predLoading) return <PageState loading error={null} />
  if (predError || !predictions) return <PageState loading={false} error={predError} />

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-[15px] font-semibold">UEFA Nations League -- international break</h1>
        <p className="max-w-3xl text-[12px] text-[var(--color-text-faint)]">
          Real 2026-27 fixtures for every UEFA member association, September-October and November match rounds.
          {predictions.moneyline_model_note && <> {predictions.moneyline_model_note}</>}
        </p>
      </div>

      {predictions.data.length === 0 ? (
        <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
          {predictions.note ?? 'No predictions available yet.'}
        </div>
      ) : (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <label htmlFor="md" className="text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">Matchday</label>
            <select
              id="md"
              value={matchday}
              onChange={(e) => setPickedMatchday(Number(e.target.value))}
              className="tnum border border-[var(--color-border)] bg-[var(--color-panel)] px-2 py-1 text-[12px]"
            >
              {matchdays.map((md) => <option key={md} value={md}>Matchday {md}</option>)}
            </select>
          </div>
          <div className="border border-[var(--color-border)]">
            {matches.map((m) => <MatchRow key={m.match_id} match={m} />)}
          </div>
        </section>
      )}
    </div>
  )
}
