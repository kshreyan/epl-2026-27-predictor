import { useDashboardJson } from '../lib/useDashboardData'
import type { Envelope, UfcRankingRow } from '../lib/types'
import { PageState } from '../components/PageState'

function WeightClassTable({ rows }: { rows: UfcRankingRow[] }) {
  const sorted = [...rows].sort((a, b) => a.rank - b.rank)
  return (
    <div className="overflow-x-auto border border-[var(--color-border)]">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
            <th className="px-2 py-1.5">#</th>
            <th className="px-2 py-1.5">Fighter</th>
            <th className="tnum px-2 py-1.5 text-right">Elo</th>
            <th className="tnum px-2 py-1.5 text-right">Real fights (total)</th>
            <th className="px-2 py-1.5 text-right">Last real fight</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.fighter} className="border-b border-[var(--color-border)] last:border-0">
              <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{r.rank}</td>
              <td className="px-2 py-1.5 font-medium">{r.fighter}</td>
              <td className="tnum px-2 py-1.5 text-right">{r.elo.toFixed(1)}</td>
              <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{r.n_real_fights_total}</td>
              <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{r.last_real_fight_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function RankingsPage({ leagueId }: { leagueId: string }) {
  const { data, error, loading } = useDashboardJson<Envelope<UfcRankingRow> & { status?: string; note?: string }>(
    `${leagueId}_fighter_rankings.json`,
  )
  if (loading || error || !data) return <PageState loading={loading} error={error} />

  if (data.data.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">
        {data.note ?? 'No fighter rankings available yet.'}
      </div>
    )
  }

  const weightClasses = [...new Set(data.data.map((r) => r.weight_class))].sort()

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="border border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2.5 text-[11px] text-[var(--color-text-dim)]">
        <span className="font-medium text-[var(--color-accent)]">Model output, not the official rankings: </span>
        {data.note ?? "This project's own real, backtested Elo rating per weight class -- not the real official UFC rankings panel, which is voted on by media."}
      </div>
      {weightClasses.map((wc) => (
        <section key={wc}>
          <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">{wc}</h2>
          <WeightClassTable rows={data.data.filter((r) => r.weight_class === wc)} />
        </section>
      ))}
    </div>
  )
}
