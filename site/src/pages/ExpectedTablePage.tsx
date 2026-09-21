import { useDashboardJson } from '../lib/useDashboardData'
import type { Envelope, ExpectedTableRow } from '../lib/types'
import { num, pct } from '../lib/format'
import { PositionBand } from '../components/PositionBand'
import { PageState } from '../components/PageState'

// MLS's real playoff field (16 of 30 teams) is nothing like a European
// "top 4" Champions League zone, and it has no real relegation at all
// -- simulate_full_season.py already writes the real playoff-cutoff
// probability into this same top_4_probability field for MLS (see
// LeagueConfig.playoff_zone_size) and a true 0% into relegation_
// probability, so only the labels/highlighting need to change here.
const TOP4_LABEL_OVERRIDES: Record<string, string> = { mls: 'Playoff' }
const NO_RELEGATION_LEAGUE_IDS = new Set(['mls'])
const HIGHLIGHT_ZONE_OVERRIDES: Record<string, number> = { mls: 16 }

export function ExpectedTablePage({ leagueId }: { leagueId: string }) {
  const { data, error, loading } = useDashboardJson<Envelope<ExpectedTableRow>>(`${leagueId}_expected_table.json`)
  if (loading || error || !data) return <PageState loading={loading} error={error} />

  const rows = [...data.data].sort((a, b) => a.expected_position - b.expected_position)
  const top4Label = TOP4_LABEL_OVERRIDES[leagueId] ?? 'Top 4'
  const hasRelegation = !NO_RELEGATION_LEAGUE_IDS.has(leagueId)
  const highlightZone = HIGHLIGHT_ZONE_OVERRIDES[leagueId] ?? 4

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <section>
        <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">
          Expected final table -- 250,000-run Monte Carlo simulation
        </h2>
        <div className="overflow-x-auto border border-[var(--color-border)]">
          <table>
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-2 py-1.5">#</th>
                <th className="px-2 py-1.5">Team</th>
                <th className="px-2 py-1.5 text-right">Pts</th>
                <th className="px-2 py-1.5 text-right">Pts range</th>
                <th className="px-2 py-1.5 text-right">GD</th>
                <th className="px-2 py-1.5 text-right">Title</th>
                <th className="px-2 py-1.5 text-right">{top4Label}</th>
                {hasRelegation && <th className="px-2 py-1.5 text-right">Releg.</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={r.team}
                  className={`border-b border-[var(--color-border)] last:border-0 ${
                    i < highlightZone ? 'bg-[var(--color-panel)]' : hasRelegation && i >= rows.length - 3 ? 'bg-[var(--color-negative)]/5' : ''
                  }`}
                >
                  <td className="tnum px-2 py-1.5 text-[var(--color-text-faint)]">{r.most_likely_finish}</td>
                  <td className="px-2 py-1.5 font-medium">{r.team}</td>
                  <td className="tnum px-2 py-1.5 text-right">{num(r.expected_points)}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[var(--color-text-faint)]">
                    {r.points_5th_percentile}-{r.points_95th_percentile}
                  </td>
                  <td className="tnum px-2 py-1.5 text-right">{r.expected_goal_difference > 0 ? '+' : ''}{num(r.expected_goal_difference)}</td>
                  <td className="tnum px-2 py-1.5 text-right text-[var(--color-accent)]">{pct(r.title_probability)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(r.top_4_probability)}</td>
                  {hasRelegation && (
                    <td className="tnum px-2 py-1.5 text-right text-[var(--color-negative)]">{pct(r.relegation_probability)}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">
          5th-95th percentile finishing position
        </h2>
        <div className="border border-[var(--color-border)] p-2">
          <PositionBand rows={rows} />
        </div>
      </section>
    </div>
  )
}
