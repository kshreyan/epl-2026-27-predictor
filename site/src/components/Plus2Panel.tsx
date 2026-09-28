import type { MarginSurvivalRow } from '../lib/types'
import { pct } from '../lib/format'
import { MarginBar, RiskLabelBadge, VerdictPill } from './MarginBar'

function FactorRow({ label, score }: { label: string; score: number | null }) {
  return (
    <div className="flex items-center justify-between gap-2 text-[11px]">
      <span className="text-[var(--color-text-faint)]">{label}</span>
      <span className="tnum">{score === null ? 'n/a (thin sample)' : `${score.toFixed(1)}/10`}</span>
    </div>
  )
}

function ValueBox({ row }: { row: MarginSurvivalRow }) {
  if (row.real_line === null || row.real_odds === null) {
    return (
      <p className="text-[10px] italic text-[var(--color-text-faint)]">
        No real market line posted for this fixture yet -- bookmakers only post close to kickoff. Verdict above is
        risk-tier only.
      </p>
    )
  }
  const gap = row.value_gap ?? 0
  const gapColor = gap > 0.02 ? 'var(--color-positive)' : gap < -0.02 ? '#e05252' : 'var(--color-text-dim)'
  const lineStr = `${row.real_line >= 0 ? '+' : ''}${row.real_line}`
  return (
    <div className="space-y-1 rounded-sm bg-[var(--color-panel)] p-2 text-[11px]">
      <div className="flex justify-between text-[var(--color-text-faint)]">
        <span>Real line ({row.real_bookmaker})</span>
        <span className="tnum">{row.team} {lineStr} @ {row.real_odds.toFixed(2)}</span>
      </div>
      <div className="flex justify-between text-[var(--color-text-faint)]">
        <span>Market-implied cover prob</span>
        <span className="tnum">{pct(row.implied_prob_at_real_line ?? 0)}</span>
      </div>
      <div className="flex justify-between text-[var(--color-text-faint)]">
        <span>Model cover prob (same line)</span>
        <span className="tnum">{pct(row.cover_prob_at_real_line ?? 0)}</span>
      </div>
      <div className="flex justify-between border-t border-[var(--color-border)] pt-1 font-medium" style={{ color: gapColor }}>
        <span>Gap</span>
        <span className="tnum">{gap >= 0 ? '+' : ''}{(gap * 100).toFixed(1)}pp</span>
      </div>
    </div>
  )
}

// One team's +2 margin-survival read-out -- shown twice per match
// (home team's card and away team's card), for every match, every
// league, every gameweek. Deliberately has no lineup/tactical-
// resilience factor: no real per-match feed for either exists in this
// project (see compute_margin_survival.py's module docstring) --
// omitted rather than faked.
export function Plus2TeamCard({ row }: { row: MarginSurvivalRow }) {
  return (
    <div className="space-y-2 border border-[var(--color-border)] p-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[12px] font-medium">
          {row.team} <span className="text-[var(--color-text-faint)]">+2.0</span>
        </span>
        <VerdictPill verdict={row.verdict} />
      </div>
      <MarginBar row={row} />
      <div className="tnum grid grid-cols-3 gap-2 border-t border-[var(--color-border)] pt-2 text-[11px]">
        <div>
          <div className="text-[var(--color-text-faint)]">Cover</div>
          <div className="font-medium">{pct(row.p_cover)}</div>
        </div>
        <div>
          <div className="text-[var(--color-text-faint)]">Push</div>
          <div className="font-medium">{pct(row.p_push)}</div>
        </div>
        <div>
          <div className="text-[var(--color-text-faint)]">3+ Loss</div>
          <div className="font-medium" style={{ color: row.p_fail > 0.09 ? '#e05252' : undefined }}>{pct(row.p_fail)}</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <RiskLabelBadge label={row.risk_label} />
      </div>
      <details className="text-[11px]">
        <summary className="cursor-pointer text-[var(--color-text-faint)]">Why +2?</summary>
        <div className="mt-2 space-y-2">
          <p className="text-[var(--color-text-faint)]">{row.why_text}</p>
          <ValueBox row={row} />
          <div className="space-y-1 border-t border-[var(--color-border)] pt-2">
            <FactorRow label="Strength gap (favorable = small gap)" score={row.factor_strength_gap_score} />
            <FactorRow label="Low-total protection" score={row.factor_low_total_score} />
            <FactorRow label="Own historical tail" score={row.factor_historical_tail_score} />
            <FactorRow label="Opponent blowout rate" score={row.factor_opponent_blowout_score} />
            <FactorRow label="Rotation/congestion signal" score={row.factor_rotation_score} />
          </div>
          <p className="text-[10px] text-[var(--color-text-faint)]">
            Lineup and in-game tactical-resilience factors are not modeled -- no real per-match data source for
            either exists in this project. Theoretical fair +2 price from this model:{' '}
            <span className="tnum">{row.fair_plus2_decimal_odds ?? 'n/a'}</span> decimal. The verdict above combines
            absolute blowout risk with real market price where one exists -- it is a synthesis of the numbers on
            this card, not separate advice.
          </p>
        </div>
      </details>
    </div>
  )
}

export function Plus2Section({ home, away }: { home?: MarginSurvivalRow; away?: MarginSurvivalRow }) {
  if (!home && !away) return null
  return (
    <div className="space-y-2 md:col-span-2">
      <h3 className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">+2 Margin Survival</h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {home && <Plus2TeamCard row={home} />}
        {away && <Plus2TeamCard row={away} />}
      </div>
    </div>
  )
}
