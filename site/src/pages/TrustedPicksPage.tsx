import { useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type {
  InternationalTrustedPicksPayload, InternationalTrustedPickRow,
  TrustedPicksPayload, TrustedPickRow,
} from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { PageState } from '../components/PageState'

const MARKET_LABEL: Record<TrustedPickRow['market'], string> = {
  moneyline: 'Moneyline', btts: 'BTTS', totals: 'Totals', spread: 'Spread',
}

function OutcomeBadge({ status, outcome }: { status: string; outcome: TrustedPickRow['outcome'] }) {
  if (status !== 'completed') {
    return <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-faint)]">upcoming</span>
  }
  if (outcome === 'win') {
    return <span className="rounded-sm bg-[var(--color-positive)]/15 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-positive)]">hit</span>
  }
  if (outcome === 'push') {
    return <span className="rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-dim)]">push</span>
  }
  return <span className="rounded-sm bg-[var(--color-negative)]/15 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-negative)]">miss</span>
}

function WeekTable({ week }: { week: { week_start: string; week_end: string; picks: TrustedPickRow[] } }) {
  const scored = week.picks.filter((p) => p.status === 'completed' && p.outcome !== 'push')
  const hits = scored.filter((p) => p.outcome === 'win').length

  return (
    <div className="border border-[var(--color-border)]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2">
        <span className="text-[12px] font-medium">
          Week of {week.week_start} <span className="text-[var(--color-text-faint)]">to {week.week_end}</span>
        </span>
        {scored.length > 0 && (
          <span className="tnum text-[11px] text-[var(--color-text-faint)]">
            {hits}/{scored.length} hit so far
          </span>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-[12px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
              <th className="px-2 py-1.5">#</th>
              <th className="px-2 py-1.5">League</th>
              <th className="px-2 py-1.5">Match</th>
              <th className="px-2 py-1.5">Kickoff</th>
              <th className="px-2 py-1.5">Market</th>
              <th className="px-2 py-1.5">Pick</th>
              <th className="px-2 py-1.5">Probability</th>
              <th className="px-2 py-1.5">Edge</th>
              <th className="px-2 py-1.5">Result</th>
            </tr>
          </thead>
          <tbody>
            {week.picks.map((p) => (
              <tr key={`${p.match_id}_${p.market}`} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-panel)]">
                <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{p.rank}</td>
                <td className="px-2 py-1.5">{p.league_display_name}</td>
                <td className="px-2 py-1.5">{p.home_team} <span className="text-[var(--color-text-faint)]">v</span> {p.away_team}</td>
                <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{formatKickoff(p.kickoff_utc)}</td>
                <td className="px-2 py-1.5 text-[var(--color-text-faint)]">{MARKET_LABEL[p.market]}</td>
                <td className="px-2 py-1.5 font-medium text-[var(--color-accent)]">
                  {p.pick}
                  {p.actual_score && <span className="ml-1.5 tnum text-[var(--color-text-faint)]">({p.actual_score})</span>}
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

function InternationalWeekTable({ week }: { week: { week_start: string; week_end: string; picks: InternationalTrustedPickRow[] } }) {
  const scored = week.picks.filter((p) => p.status === 'completed' && p.outcome !== 'push')
  const hits = scored.filter((p) => p.outcome === 'win').length

  return (
    <div className="border border-[var(--color-border)]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2">
        <span className="text-[12px] font-medium">
          Week of {week.week_start} <span className="text-[var(--color-text-faint)]">to {week.week_end}</span>
        </span>
        {scored.length > 0 && (
          <span className="tnum text-[11px] text-[var(--color-text-faint)]">{hits}/{scored.length} hit so far</span>
        )}
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
                  {p.pick}
                  {p.actual_score && <span className="ml-1.5 tnum text-[var(--color-text-faint)]">({p.actual_score})</span>}
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

export function TrustedPicksPage() {
  const { data, error, loading } = useDashboardJson<TrustedPicksPayload>('trusted_picks.json')
  const { data: intl, error: intlError, loading: intlLoading } =
    useDashboardJson<InternationalTrustedPicksPayload>('international_trusted_picks.json')
  const [visibleCount, setVisibleCount] = useState(4)
  const [intlVisibleCount, setIntlVisibleCount] = useState(3)

  if (loading || error || !data) return <PageState loading={loading} error={error} />

  const weeks = data.weeks.slice(0, visibleCount)
  const intlWeeks = (intl?.weeks ?? []).slice(0, intlVisibleCount)

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-6">
      <div className="space-y-4">
        <div className="space-y-1">
          <h1 className="text-[15px] font-semibold">Most trusted predictions</h1>
          <p className="max-w-3xl text-[12px] text-[var(--color-text-faint)]">
            The 15 highest-edge picks each week, pooled across every league (Premier League, La Liga, Serie A, Bundesliga,
            Ligue 1) and every market (moneyline, BTTS, spread, totals). Ranked by edge over baseline -- predicted
            probability minus the market's naive baseline (1/3 for moneyline, 1/2 for the binary markets) -- so a lopsided
            BTTS call in a blowout isn't ranked above a genuinely confident moneyline pick just because binary markets sit
            above 50% more often.
          </p>
        </div>
        {data.weeks.length === 0 ? (
          <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
            No predictions available yet.
          </div>
        ) : (
          <div className="space-y-4">
            {weeks.map((w) => (
              <WeekTable key={w.week_start} week={w} />
            ))}
          </div>
        )}
        {visibleCount < data.weeks.length && (
          <button
            onClick={() => setVisibleCount((c) => c + 4)}
            className="w-full border border-[var(--color-border)] px-3 py-2 text-[11px] text-[var(--color-text-dim)] hover:bg-[var(--color-panel)]"
          >
            Show earlier weeks
          </button>
        )}
      </div>

      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-[13px] font-semibold">International break -- UEFA Nations League</h2>
          <p className="max-w-3xl text-[12px] text-[var(--color-text-faint)]">
            The top 15 highest-confidence Nations League moneyline picks each week. Moneyline only here, unlike the
            domestic table above: BTTS/spread/totals for this competition are Simple-Poisson-derived and were never
            independently backtested for those markets, so they're left out of a table meant to surface what's
            actually validated -- see the International Break page for the full picture.
          </p>
        </div>
        {intlLoading || intlError || !intl ? (
          <PageState loading={intlLoading} error={intlError} />
        ) : intl.weeks.length === 0 ? (
          <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
            {intl.note ?? 'No international predictions available yet.'}
          </div>
        ) : (
          <div className="space-y-4">
            {intlWeeks.map((w) => (
              <InternationalWeekTable key={w.week_start} week={w} />
            ))}
            {intlVisibleCount < intl.weeks.length && (
              <button
                onClick={() => setIntlVisibleCount((c) => c + 3)}
                className="w-full border border-[var(--color-border)] px-3 py-2 text-[11px] text-[var(--color-text-dim)] hover:bg-[var(--color-panel)]"
              >
                Show more weeks
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
