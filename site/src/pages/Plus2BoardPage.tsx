import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardJson } from '../lib/useDashboardData'
import type { MarginSurvivalRow, Top20MarginSurvivalPayload } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { PageState } from '../components/PageState'
import { VerdictPill } from '../components/MarginBar'

// Cross-league, not scoped to any one competition -- reachable from any
// league's tab bar, same pattern as InternationalBreakPage.
export function Plus2BoardPage() {
  const { data, error, loading } = useDashboardJson<Top20MarginSurvivalPayload>('top20_margin_survival.json')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (loading) return <PageState loading error={null} />
  if (error || !data) return <PageState loading={false} error={error} />

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-[15px] font-semibold">Top 20 +2 Margin Survival Opportunities</h1>
        <p className="max-w-3xl text-[12px] text-[var(--color-text-faint)]">
          Every team, every match, every league, every gameweek gets a real blowout-risk read and a verdict
          (<strong>Pick</strong> / <strong>Lean</strong> / Pass) that combines that risk with real market price
          where one currently exists -- each at that league's own real threshold (+2 goals for soccer/UEFA, +14
          points for NFL, +20 points for NBA; see each row's own verdict and the expanded "why" text). Ranked by
          verdict first, then by real price value, then by lowest blowout risk -- Pass is excluded from this
          board entirely.
        </p>
        {data.note && <p className="max-w-3xl text-[11px] italic text-[var(--color-text-faint)]">{data.note}</p>}
      </div>

      {data.data.length === 0 ? (
        <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
          No upcoming fixtures right now.
        </div>
      ) : (
        <div className="overflow-x-auto border border-[var(--color-border)]">
          <table className="tnum w-full text-[12px]">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-2 py-2">#</th>
                <th className="px-2 py-2">Verdict</th>
                <th className="px-2 py-2">Team</th>
                <th className="px-2 py-2">Opponent</th>
                <th className="px-2 py-2">League</th>
                <th className="px-2 py-2">H/A</th>
                <th className="px-2 py-2">Kickoff</th>
                <th className="px-2 py-2">Predicted</th>
                <th className="px-2 py-2">Blowout Loss</th>
                <th className="px-2 py-2">Real line</th>
                <th className="px-2 py-2">Value gap</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((row) => {
                // UFC's real row shape has no team/is_home/predicted_score
                // (an individual fight has no team or home/away, and no
                // real score to predict -- see UfcMarginSurvivalRow).
                const isUfc = row.league_id === 'ufc'
                const name = isUfc ? (row as { fighter: string }).fighter : (row as { team: string }).team
                const rowKey = row.match_id + name
                const fixturesPath = isUfc ? `/ufc/fightcard` : `/${row.league_id}/fixtures`
                const predicted = isUfc ? '—' : (row as { predicted_score_model_only: string }).predicted_score_model_only
                return (
                  <>
                    <tr
                      key={rowKey}
                      className="cursor-pointer border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-panel)]"
                      onClick={() => setExpandedId((id) => (id === rowKey ? null : rowKey))}
                    >
                      <td className="px-2 py-2">{row.rank}</td>
                      <td className="px-2 py-2"><VerdictPill verdict={row.verdict} /></td>
                      <td className="px-2 py-2 font-medium">{name}</td>
                      <td className="px-2 py-2 text-[var(--color-text-faint)]">{row.opponent}</td>
                      <td className="px-2 py-2">
                        <Link
                          to={fixturesPath}
                          onClick={(e) => e.stopPropagation()}
                          className="text-[var(--color-accent)] hover:underline"
                        >
                          {row.league_display_name}
                        </Link>
                      </td>
                      <td className="px-2 py-2">{isUfc ? '—' : (row as { is_home: boolean }).is_home ? 'H' : 'A'}</td>
                      <td className="px-2 py-2 text-[var(--color-text-faint)]">{formatKickoff(row.kickoff_utc)}</td>
                      <td className="px-2 py-2">{predicted}</td>
                      <td className="px-2 py-2">{pct(row.p_fail)}</td>
                      {(() => {
                        // UFC has no real spread market at all (see
                        // UfcMarginSurvivalRow) -- real_line/real_odds/
                        // value_gap simply don't exist on that row shape.
                        const realLine = isUfc ? null : (row as MarginSurvivalRow).real_line
                        const realOdds = isUfc ? null : (row as MarginSurvivalRow).real_odds
                        const valueGap = isUfc ? null : (row as MarginSurvivalRow).value_gap
                        return (
                          <>
                            <td className="px-2 py-2 text-[var(--color-text-faint)]">
                              {realLine === null ? '—' : `${realLine >= 0 ? '+' : ''}${realLine} @ ${realOdds?.toFixed(2)}`}
                            </td>
                            <td className="px-2 py-2" style={{ color: (valueGap ?? 0) > 0.02 ? 'var(--color-positive)' : (valueGap ?? 0) < -0.02 ? '#e05252' : undefined }}>
                              {valueGap === null ? '—' : `${valueGap >= 0 ? '+' : ''}${(valueGap * 100).toFixed(1)}pp`}
                            </td>
                          </>
                        )
                      })()}
                    </tr>
                    {expandedId === rowKey && (
                      <tr className="border-b border-[var(--color-border)] bg-[var(--color-panel)]">
                        <td colSpan={11} className="px-3 py-3 text-[11px] text-[var(--color-text-faint)]">
                          {row.why_text}
                        </td>
                      </tr>
                    )}
                  </>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
