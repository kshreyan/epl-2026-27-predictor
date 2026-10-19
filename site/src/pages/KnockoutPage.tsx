import { useDashboardJson } from '../lib/useDashboardData'
import type { KnockoutProbabilityPayload } from '../lib/types'
import { pct } from '../lib/format'
import { PageState } from '../components/PageState'

export function KnockoutPage({ leagueId }: { leagueId: string }) {
  const { data, error, loading } = useDashboardJson<KnockoutProbabilityPayload>(`${leagueId}_knockout_probabilities.json`)
  if (loading || error || !data) return <PageState loading={loading} error={error} />

  if (data.data.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">
        {data.note ?? 'No knockout-bracket simulation available yet.'}
      </div>
    )
  }

  const rows = [...data.data].sort((a, b) => b.prob_win_competition - a.prob_win_competition)

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="border border-[var(--color-negative)]/40 bg-[var(--color-negative)]/5 px-3 py-2.5 text-[11px] text-[var(--color-text-dim)]">
        <span className="font-medium text-[var(--color-negative)]">Read with real caution: </span>
        {data.note ?? 'Monte Carlo projection of the rest of the real league phase and the real knockout bracket, which has not been drawn yet.'}
        {data.n_trials && <span className="tnum text-[var(--color-text-faint)]"> ({data.n_trials.toLocaleString()} simulated trials.)</span>}
      </div>

      <section>
        <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">
          Projected path through the real knockout bracket
        </h2>
        <div className="overflow-x-auto border border-[var(--color-border)]">
          <table>
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-2 py-1.5">#</th>
                <th className="px-2 py-1.5">Team</th>
                <th className="tnum px-2 py-1.5 text-right">Elo</th>
                <th className="tnum px-2 py-1.5 text-right">Pts</th>
                <th className="px-2 py-1.5 text-right">Direct R16</th>
                <th className="px-2 py-1.5 text-right">Play-off</th>
                <th className="px-2 py-1.5 text-right">Reach R16</th>
                <th className="px-2 py-1.5 text-right">Reach QF</th>
                <th className="px-2 py-1.5 text-right">Reach SF</th>
                <th className="px-2 py-1.5 text-right">Reach Final</th>
                <th className="px-2 py-1.5 text-right">Win it</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.team} className={`border-b border-[var(--color-border)] last:border-0 ${i < 8 ? 'bg-[var(--color-panel)]' : ''}`}>
                  <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{i + 1}</td>
                  <td className="px-2 py-1.5 font-medium">{r.team}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{Math.round(r.current_elo)}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{r.current_points}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_direct_round_of_16)}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">{pct(r.prob_playoff_round_zone)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_reach_round_of_16)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_reach_quarter_final)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_reach_semi_final)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.prob_reach_final)}</td>
                  <td className="tnum px-2 py-1.5 text-right font-medium text-[var(--color-accent)]">{pct(r.prob_win_competition)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
