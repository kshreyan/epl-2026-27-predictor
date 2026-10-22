import { useDashboardJson } from '../lib/useDashboardData'
import type { PlayoffPicturePayload, PlayoffPictureRow } from '../lib/types'
import { pct, num } from '../lib/format'
import { PageState } from '../components/PageState'

function ConferenceTable({ rows, hasDivisionWinner }: { rows: PlayoffPictureRow[]; hasDivisionWinner: boolean }) {
  const sorted = [...rows].sort((a, b) => b.prob_make_playoffs - a.prob_make_playoffs)
  return (
    <div className="overflow-x-auto border border-[var(--color-border)]">
      <table>
        <thead>
          <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
            <th className="px-2 py-1.5">#</th>
            <th className="px-2 py-1.5">Team</th>
            <th className="px-2 py-1.5">Division</th>
            <th className="tnum px-2 py-1.5 text-right">Win %</th>
            <th className="tnum px-2 py-1.5 text-right">Pt Diff</th>
            <th className="px-2 py-1.5 text-right">Make Playoffs</th>
            <th className="px-2 py-1.5 text-right">Direct Seed</th>
            {hasDivisionWinner && <th className="px-2 py-1.5 text-right">Win Division</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={r.team} className={`border-b border-[var(--color-border)] last:border-0 ${i < (hasDivisionWinner ? 7 : 8) ? 'bg-[var(--color-panel)]' : ''}`}>
              <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{i + 1}</td>
              <td className="px-2 py-1.5 font-medium">{r.team}</td>
              <td className="px-2 py-1.5 text-[var(--color-text-faint)]">{r.division}</td>
              <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{r.current_win_pct !== null ? num(r.current_win_pct, 3) : '—'}</td>
              <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{r.current_point_diff > 0 ? '+' : ''}{r.current_point_diff}</td>
              <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_make_playoffs)}</td>
              <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_direct_seed)}</td>
              {hasDivisionWinner && (
                <td className="tnum px-2 py-1.5 text-right font-medium text-[var(--color-accent)]">
                  {typeof r.prob_win_division === 'number' ? pct(r.prob_win_division) : '—'}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function StandingsPage({ leagueId }: { leagueId: string }) {
  const { data, error, loading } = useDashboardJson<PlayoffPicturePayload>(`${leagueId}_playoff_picture.json`)
  if (loading || error || !data) return <PageState loading={loading} error={error} />

  if (data.data.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">
        {data.note ?? 'No season/playoff-picture simulation available yet.'}
      </div>
    )
  }

  const hasDivisionWinner = data.data.some((r) => typeof r.prob_win_division === 'number')
  const conferences = [...new Set(data.data.map((r) => r.conference))].sort()

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="border border-[var(--color-negative)]/40 bg-[var(--color-negative)]/5 px-3 py-2.5 text-[11px] text-[var(--color-text-dim)]">
        <span className="font-medium text-[var(--color-negative)]">Read with real caution: </span>
        {data.note ?? 'Monte Carlo projection of the rest of the real regular season -- who makes the playoffs and as what seed, not the playoff bracket itself.'}
        {data.n_trials && <span className="tnum text-[var(--color-text-faint)]"> ({data.n_trials.toLocaleString()} simulated trials.)</span>}
      </div>

      {conferences.map((conf) => (
        <section key={conf}>
          <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">{conf}</h2>
          <ConferenceTable rows={data.data.filter((r) => r.conference === conf)} hasDivisionWinner={hasDivisionWinner} />
        </section>
      ))}
    </div>
  )
}
