import type { MarginSurvivalRow } from '../lib/types'
import { pct } from '../lib/format'
import { MarginBar, RiskLabelBadge } from './MarginBar'

function FactorRow({ label, score }: { label: string; score: number | null }) {
  return (
    <div className="flex items-center justify-between gap-2 text-[11px]">
      <span className="text-[var(--color-text-faint)]">{label}</span>
      <span className="tnum">{score === null ? 'n/a (thin sample)' : `${score.toFixed(1)}/10`}</span>
    </div>
  )
}

// One team's +2 margin-survival read-out -- shown twice per eligible
// match (home team's card and away team's card), since either side can
// be the +2 candidate. Deliberately has no lineup/tactical-resilience
// factor: no real per-match feed for either exists in this project (see
// compute_margin_survival.py's module docstring) -- omitted rather than
// faked.
export function Plus2TeamCard({ row }: { row: MarginSurvivalRow }) {
  return (
    <div className="space-y-2 border border-[var(--color-border)] p-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[12px] font-medium">
          {row.team} <span className="text-[var(--color-text-faint)]">+2.0</span>
        </span>
        <RiskLabelBadge label={row.risk_label} />
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
      <details className="text-[11px]">
        <summary className="cursor-pointer text-[var(--color-text-faint)]">Why +2?</summary>
        <div className="mt-2 space-y-2">
          <p className="text-[var(--color-text-faint)]">{row.why_text}</p>
          <div className="space-y-1 border-t border-[var(--color-border)] pt-2">
            <FactorRow label="Strength gap (favorable = small gap)" score={row.factor_strength_gap_score} />
            <FactorRow label="Low-total protection" score={row.factor_low_total_score} />
            <FactorRow label="Own historical tail" score={row.factor_historical_tail_score} />
            <FactorRow label="Opponent blowout rate" score={row.factor_opponent_blowout_score} />
            <FactorRow label="Rotation/congestion signal" score={row.factor_rotation_score} />
          </div>
          <p className="text-[10px] text-[var(--color-text-faint)]">
            Lineup and in-game tactical-resilience factors are not modeled -- no real per-match data source for
            either exists in this project. Model fair +2 price (from these probabilities) vs. the market's actual
            price is not shown yet: this project's real +2.0 Asian Handicap market coverage is too sparse to
            price fairly (see the model performance page).
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
