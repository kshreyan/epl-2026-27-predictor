import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardJson } from '../lib/useDashboardData'
import type { Top20MarginSurvivalPayload } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { PageState } from '../components/PageState'
import { RiskLabelBadge } from '../components/MarginBar'

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
          Teams from close-scoreline matches with the lowest modeled probability of a 3+ goal defeat -- the +2.0
          Asian Handicap's actual losing condition. Phase 1: <strong>Safest</strong> only, ranked purely by lowest
          P(lose by 3+). This naturally surfaces heavy favorites that may have little real betting value at their
          market price -- a market-value-aware ranking ("Best Value" / "Best Balance") needs reliable real +2.0
          market coverage, which this project does not have yet (see note below).
        </p>
        {data.note && <p className="max-w-3xl text-[11px] italic text-[var(--color-text-faint)]">{data.note}</p>}
      </div>

      {data.data.length === 0 ? (
        <div className="border border-[var(--color-border)] px-3 py-8 text-center text-[12px] text-[var(--color-text-faint)]">
          No eligible upcoming fixtures right now.
        </div>
      ) : (
        <div className="overflow-x-auto border border-[var(--color-border)]">
          <table className="tnum w-full text-[12px]">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-2 py-2">#</th>
                <th className="px-2 py-2">Team</th>
                <th className="px-2 py-2">Opponent</th>
                <th className="px-2 py-2">League</th>
                <th className="px-2 py-2">H/A</th>
                <th className="px-2 py-2">Kickoff</th>
                <th className="px-2 py-2">Predicted</th>
                <th className="px-2 py-2">Cover</th>
                <th className="px-2 py-2">Push</th>
                <th className="px-2 py-2">3+ Loss</th>
                <th className="px-2 py-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((row) => (
                <>
                  <tr
                    key={row.match_id + row.team}
                    className="cursor-pointer border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-panel)]"
                    onClick={() => setExpandedId((id) => (id === row.match_id + row.team ? null : row.match_id + row.team))}
                  >
                    <td className="px-2 py-2">{row.rank}</td>
                    <td className="px-2 py-2 font-medium">{row.team}</td>
                    <td className="px-2 py-2 text-[var(--color-text-faint)]">{row.opponent}</td>
                    <td className="px-2 py-2">
                      <Link
                        to={`/${row.league_id}/fixtures`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-[var(--color-accent)] hover:underline"
                      >
                        {row.league_display_name}
                      </Link>
                    </td>
                    <td className="px-2 py-2">{row.is_home ? 'H' : 'A'}</td>
                    <td className="px-2 py-2 text-[var(--color-text-faint)]">{formatKickoff(row.kickoff_utc)}</td>
                    <td className="px-2 py-2">{row.predicted_score_model_only}</td>
                    <td className="px-2 py-2">{pct(row.p_cover)}</td>
                    <td className="px-2 py-2">{pct(row.p_push)}</td>
                    <td className="px-2 py-2">{pct(row.p_fail)}</td>
                    <td className="px-2 py-2"><RiskLabelBadge label={row.risk_label} /></td>
                  </tr>
                  {expandedId === row.match_id + row.team && (
                    <tr className="border-b border-[var(--color-border)] bg-[var(--color-panel)]">
                      <td colSpan={11} className="px-3 py-3 text-[11px] text-[var(--color-text-faint)]">
                        {row.why_text}
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
