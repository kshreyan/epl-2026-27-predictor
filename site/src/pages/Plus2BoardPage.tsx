import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardJson } from '../lib/useDashboardData'
import type { PickMoneylinePayload, Top20MarginSurvivalPayload } from '../lib/types'
import { formatKickoff, pct } from '../lib/format'
import { PageState } from '../components/PageState'
import { PickMoneylineBadge, VerdictPill } from '../components/MarginBar'

// Spotlight list for the compound "Pick Moneyline" signal (see
// build_margin_survival_json.py's _flag_pick_moneyline()): a real
// ELITE SURVIVAL PICK verdict, a HIGH BLOWOUT RISK opponent, a better
// own predicted scoreline, AND a real top-quartile-vs-bottom-half gap
// in the current standings, all at once -- checked across every real
// upcoming fixture in every league, not just the next round/slate.
function PickMoneylineSpotlight() {
  const { data, error, loading } = useDashboardJson<PickMoneylinePayload>('pick_moneyline.json')
  if (loading || error || !data || data.data.length === 0) return null

  return (
    <div className="space-y-2">
      <h2 className="text-[13px] font-semibold">Pick Moneyline</h2>
      {data.note && <p className="max-w-3xl text-[11px] italic text-[var(--color-text-faint)]">{data.note}</p>}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {data.data.map((row) => (
          <Link
            key={row.match_id + row.team}
            to={`/${row.league_id}/fixtures`}
            className="block space-y-1.5 border border-[var(--color-border)] p-2.5 hover:bg-[var(--color-panel)]"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-medium text-[var(--color-text-faint)]">{row.league_display_name}</span>
              <PickMoneylineBadge />
            </div>
            <div className="text-[13px] font-medium">
              {row.team} <span className="text-[var(--color-text-faint)]">({row.predicted_score_model_only})</span>
            </div>
            <div className="text-[11px] text-[var(--color-text-faint)]">
              vs {row.opponent} -- {formatKickoff(row.kickoff_utc)}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

// Cross-league, not scoped to any one competition -- reachable from any
// league's tab bar, same pattern as InternationalBreakPage.
export function Plus2BoardPage() {
  const { data, error, loading } = useDashboardJson<Top20MarginSurvivalPayload>('top20_margin_survival.json')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (loading) return <PageState loading error={null} />
  if (error || !data) return <PageState loading={false} error={error} />

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <PickMoneylineSpotlight />
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
              {data.data.map((row) => (
                <>
                  <tr
                    key={row.match_id + row.team}
                    className="cursor-pointer border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-panel)]"
                    onClick={() => setExpandedId((id) => (id === row.match_id + row.team ? null : row.match_id + row.team))}
                  >
                    <td className="px-2 py-2">{row.rank}</td>
                    <td className="px-2 py-2"><VerdictPill verdict={row.verdict} /></td>
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
                    <td className="px-2 py-2">{pct(row.p_fail)}</td>
                    <td className="px-2 py-2 text-[var(--color-text-faint)]">
                      {row.real_line === null ? '—' : `${row.real_line >= 0 ? '+' : ''}${row.real_line} @ ${row.real_odds?.toFixed(2)}`}
                    </td>
                    <td className="px-2 py-2" style={{ color: (row.value_gap ?? 0) > 0.02 ? 'var(--color-positive)' : (row.value_gap ?? 0) < -0.02 ? '#e05252' : undefined }}>
                      {row.value_gap === null ? '—' : `${row.value_gap >= 0 ? '+' : ''}${(row.value_gap * 100).toFixed(1)}pp`}
                    </td>
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
