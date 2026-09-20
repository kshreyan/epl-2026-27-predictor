import { useMemo, useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type {
  InternationalTrustedPicksPayload, InternationalTrustedPickRow,
  NationsLeagueMatchRow, NationsLeaguePredictionsPayload,
} from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
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
        <span className="tnum text-center text-[13px] font-medium text-[var(--color-accent)]">{match.predicted_score}</span>
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

function OutcomeBadge({ status, outcome }: { status: string; outcome: InternationalTrustedPickRow['outcome'] }) {
  if (status !== 'completed') {
    return <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">upcoming</span>
  }
  if (outcome === 'win') return <span className="rounded-sm bg-[var(--color-positive)]/15 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-positive)]">hit</span>
  if (outcome === 'push') return <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-dim)]">push</span>
  return <span className="rounded-sm bg-[var(--color-negative)]/15 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-negative)]">miss</span>
}

function TrustedPicksWeekTable({ week }: { week: { week_start: string; week_end: string; picks: InternationalTrustedPickRow[] } }) {
  const scored = week.picks.filter((p) => p.status === 'completed' && p.outcome !== 'push')
  const hits = scored.filter((p) => p.outcome === 'win').length
  return (
    <div className="border border-[var(--color-border)]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2">
        <span className="text-[12px] font-medium">
          Week of {week.week_start} <span className="text-[var(--color-text-faint)]">to {week.week_end}</span>
        </span>
        {scored.length > 0 && <span className="tnum text-[11px] text-[var(--color-text-faint)]">{hits}/{scored.length} hit so far</span>}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-[12px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
              <th className="px-2 py-1.5">#</th>
              <th className="px-2 py-1.5">Match</th>
              <th className="px-2 py-1.5">Group</th>
              <th className="px-2 py-1.5">Kickoff</th>
              <th className="px-2 py-1.5">Pick</th>
              <th className="px-2 py-1.5">Probability</th>
              <th className="px-2 py-1.5">Edge</th>
              <th className="px-2 py-1.5">Result</th>
            </tr>
          </thead>
          <tbody>
            {week.picks.map((p) => (
              <tr key={p.match_id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-panel)]">
                <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{p.rank}</td>
                <td className="px-2 py-1.5">{p.home_team} <span className="text-[var(--color-text-faint)]">v</span> {p.away_team}</td>
                <td className="px-2 py-1.5 text-[var(--color-text-faint)]">{p.group}</td>
                <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{formatKickoff(p.kickoff_utc)}</td>
                <td className="px-2 py-1.5 font-medium text-[var(--color-accent)]">
                  {p.pick}{p.actual_score && <span className="ml-1.5 tnum text-[var(--color-text-faint)]">({p.actual_score})</span>}
                </td>
                <td className="tnum px-2 py-1.5">{pct(p.probability)}</td>
                <td className="tnum px-2 py-1.5">+{pct(p.edge)}</td>
                <td className="px-2 py-1.5"><OutcomeBadge status={p.status} outcome={p.outcome} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function InternationalBreakPage() {
  const { data: predictions, error: predError, loading: predLoading } =
    useDashboardJson<NationsLeaguePredictionsPayload>('nations_league_match_predictions.json')
  const { data: trusted, error: trustedError, loading: trustedLoading } =
    useDashboardJson<InternationalTrustedPicksPayload>('international_trusted_picks.json')
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

  if (predLoading || trustedLoading) return <PageState loading error={null} />
  if (predError || trustedError || !predictions || !trusted) return <PageState loading={false} error={predError ?? trustedError} />

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

      <section className="space-y-3">
        <div className="space-y-1">
          <h2 className="text-[13px] font-semibold">Trusted picks</h2>
          <p className="max-w-3xl text-[12px] text-[var(--color-text-faint)]">{trusted.ranking_method}</p>
        </div>
        {trusted.weeks.length === 0 ? (
          <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
            {trusted.note ?? 'No trusted picks available yet.'}
          </div>
        ) : (
          <div className="space-y-4">
            {trusted.weeks.map((w) => <TrustedPicksWeekTable key={w.week_start} week={w} />)}
          </div>
        )}
      </section>
    </div>
  )
}
