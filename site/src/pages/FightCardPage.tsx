import { useMemo, useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type { Envelope, UfcFightRow, UfcMarginSurvivalRow } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { Plus2Section } from '../components/Plus2Panel'
import { PageState } from '../components/PageState'

function ProbBar({ a, b }: { a: number; b: number }) {
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-sm">
      <div style={{ width: `${a * 100}%` }} className="bg-[var(--color-accent)]" title={`Fighter A ${pct(a)}`} />
      <div style={{ width: `${b * 100}%` }} className="bg-[var(--color-positive)]" title={`Fighter B ${pct(b)}`} />
    </div>
  )
}

function FightRow({ fight, margin }: { fight: UfcFightRow; margin?: { a?: UfcMarginSurvivalRow; b?: UfcMarginSurvivalRow } }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="grid w-full grid-cols-[100px_1fr_120px_140px_auto] items-center gap-3 px-2 py-2 text-left hover:bg-[var(--color-panel)]"
      >
        <span className="tnum text-[11px] text-[var(--color-text-faint)]">{formatKickoff(fight.kickoff_utc)}</span>
        <span className="text-[12px]">
          {fight.fighter_a} <span className="text-[var(--color-text-faint)]">vs</span> {fight.fighter_b}
          <span className="ml-2 text-[10px] text-[var(--color-text-faint)]">{fight.weight_class}</span>
        </span>
        <span className="text-center">
          <span className="tnum block text-[12px] font-medium text-[var(--color-accent)]">{fight.predicted_outcome}</span>
          {fight.status === 'completed' && fight.actual_winner && (
            <span className="tnum block text-[10px] text-[var(--color-text-faint)]">
              {fight.actual_winner} by {fight.actual_method}{fight.actual_finish_round ? ` (Rd ${fight.actual_finish_round})` : ''}
            </span>
          )}
        </span>
        <ProbBar a={fight.fighter_a_win_prob} b={fight.fighter_b_win_prob} />
        <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
          {fight.market_available ? 'MODEL + MARKET' : 'MODEL-ONLY'} · DQ {fight.data_quality_score}
        </span>
      </button>
      {open && (
        <div className="grid grid-cols-1 gap-4 border-t border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-3 md:grid-cols-2">
          <div className="space-y-2 text-[11px]">
            <h3 className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Model vs. market</h3>
            <div className="tnum grid grid-cols-2 gap-2">
              <div>
                <div className="text-[var(--color-text-faint)]">{fight.fighter_a}</div>
                <div>{pct(fight.fighter_a_win_prob)}</div>
              </div>
              <div>
                <div className="text-[var(--color-text-faint)]">{fight.fighter_b}</div>
                <div>{pct(fight.fighter_b_win_prob)}</div>
              </div>
            </div>
            <p className="text-[var(--color-text-faint)]">
              {fight.market_available
                ? `Real market odds: ${fight.fighter_a} @ ${fight.market_fighter_a_odds?.toFixed(2)}, ${fight.fighter_b} @ ${fight.market_fighter_b_odds?.toFixed(2)} (moneyline only -- no real spread/totals market exists for an individual fight).`
                : 'No market data available -- no live odds feed is configured, or no bookmaker has posted this fight yet (model-only prediction).'}
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                scheduled rounds: {fight.scheduled_rounds}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                {fight.fighter_a} Elo: {fight.fighter_a_elo}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                {fight.fighter_b} Elo: {fight.fighter_b_elo}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                confidence: {pct(fight.confidence)}
              </span>
              <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">
                upset risk: {pct(fight.upset_risk)}
              </span>
            </div>
          </div>
          <Plus2Section home={margin?.a} away={margin?.b} />
        </div>
      )}
    </div>
  )
}

export function FightCardPage({ leagueId }: { leagueId: string }) {
  const { data, error, loading } = useDashboardJson<Envelope<UfcFightRow>>(`${leagueId}_match_predictions.json`)
  const { data: marginData } = useDashboardJson<Envelope<UfcMarginSurvivalRow>>(`${leagueId}_margin_survival.json`)
  const [pickedEventId, setPickedEventId] = useState<string | null>(null)

  const marginByMatch = useMemo(() => {
    const map = new Map<string, { a?: UfcMarginSurvivalRow; b?: UfcMarginSurvivalRow }>()
    for (const row of marginData?.data ?? []) {
      const entry = map.get(row.match_id) ?? {}
      if (!entry.a) entry.a = row
      else entry.b = row
      map.set(row.match_id, entry)
    }
    return map
  }, [marginData])

  const events = useMemo(() => {
    if (!data) return []
    const seen = new Map<string, { event_id: string; event_name: string; date: string }>()
    for (const f of data.data) {
      if (!seen.has(f.event_id)) seen.set(f.event_id, { event_id: f.event_id, event_name: f.event_name, date: f.date })
    }
    return [...seen.values()].sort((a, b) => a.date.localeCompare(b.date))
  }, [data])

  const defaultEventId = useMemo(() => {
    if (!data) return null
    const upcoming = events.find((e) => data.data.some((f) => f.event_id === e.event_id && f.status !== 'completed'))
    return upcoming?.event_id ?? events[events.length - 1]?.event_id ?? null
  }, [data, events])
  const eventId = pickedEventId ?? defaultEventId

  const fights = useMemo(
    () => (data ? data.data.filter((f) => f.event_id === eventId).sort((a, b) => a.kickoff_utc.localeCompare(b.kickoff_utc)) : []),
    [data, eventId],
  )

  if (loading || error || !data) return <PageState loading={loading} error={error} />

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="flex items-center gap-2">
        <label htmlFor="ev" className="text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">
          Event
        </label>
        <select
          id="ev"
          value={eventId ?? ''}
          onChange={(e) => setPickedEventId(e.target.value)}
          className="border border-[var(--color-border)] bg-[var(--color-panel)] px-2 py-1 text-[12px]"
        >
          {events.map((e) => (
            <option key={e.event_id} value={e.event_id}>
              {e.event_name}
            </option>
          ))}
        </select>
      </div>
      <div className="border border-[var(--color-border)]">
        {fights.map((f) => (
          <FightRow key={f.match_id} fight={f} margin={marginByMatch.get(f.match_id)} />
        ))}
      </div>
    </div>
  )
}
