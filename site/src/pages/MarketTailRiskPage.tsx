import { useState } from 'react'
import { useDashboardJson } from '../lib/useDashboardData'
import type { MarketTailRiskPayload, MarketTailRiskRow } from '../lib/types'
import { pct } from '../lib/format'
import { PageState } from '../components/PageState'
import { RiskLabelBadge } from '../components/MarginBar'

// A single real instrument's own tail-risk card -- the markets
// equivalent of Plus2TeamCard, but for one instrument, not a two-team
// matchup (no opponent, no verdict/real-market-price comparison: the
// instrument's own price already IS the real market's assessment).
//
// Fixed income & credit is a genuinely different real unit: FRED's
// `current_price`/`threshold` are a yield/spread LEVEL (percentage
// points), not a tradeable price or a %-return -- see
// compute_market_tail_risk.py's module docstring.
function TailRiskCard({ row, isFixedIncome }: { row: MarketTailRiskRow; isFixedIncome: boolean }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="space-y-2 border border-[var(--color-border)] p-2.5">
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between gap-2 text-left">
        <span className="text-[13px] font-medium">{row.ticker}</span>
        <RiskLabelBadge label={row.risk_label} />
      </button>
      <div className="tnum flex items-baseline justify-between text-[12px]">
        <span className="text-[var(--color-text-faint)]">{isFixedIncome ? 'Yield/Spread' : 'Price'}</span>
        <span className="font-medium">
          {isFixedIncome ? `${row.current_price.toFixed(2)}%` : `${row.currency} ${row.current_price.toLocaleString()}`}
        </span>
      </div>
      <div className="tnum grid grid-cols-2 gap-2 border-t border-[var(--color-border)] pt-2 text-[11px]">
        <div>
          <div className="text-[var(--color-text-faint)]">Survive {row.horizon_days}d</div>
          <div className="font-medium">{pct(row.p_survive)}</div>
        </div>
        <div>
          <div className="text-[var(--color-text-faint)]">Fail {row.horizon_days}d</div>
          <div className="font-medium" style={{ color: row.p_fail > 0.2 ? '#e05252' : undefined }}>{pct(row.p_fail)}</div>
        </div>
      </div>
      {open && (
        <div className="space-y-1 border-t border-[var(--color-border)] pt-2 text-[11px] text-[var(--color-text-faint)]">
          <p>{row.why_text}</p>
          <p className="tnum">
            Adverse threshold: -{isFixedIncome ? `${row.threshold.toFixed(3)} pts` : pct(row.threshold)} over{' '}
            {row.horizon_days} trading days.
          </p>
        </div>
      )}
    </div>
  )
}

export function MarketTailRiskPage({ marketId }: { marketId: string }) {
  const { data, error, loading } = useDashboardJson<MarketTailRiskPayload>(`${marketId}_tail_risk.json`)
  if (loading) return <PageState loading error={null} />
  if (error || !data) return <PageState loading={false} error={error} />

  const sorted = [...data.data].sort((a, b) => b.p_fail - a.p_fail)
  const isFixedIncome = data.asset_class === 'fixed_income_credit'

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-[15px] font-semibold">
          {data.display_name} <span className="text-[var(--color-accent)]">Tail Risk</span>
        </h1>
        {data.engine_note && <p className="max-w-3xl text-[11px] text-[var(--color-text-faint)]">{data.engine_note}</p>}
        <p className="text-[10px] font-semibold uppercase tracking-wide text-[#e05252]">
          Not investment advice. A real, backtested volatility read only -- never a directional (up/down) call,
          never personalized to any portfolio.
        </p>
        {data.market_id === 'india_digital_assets' && (
          <p className="max-w-3xl text-[11px] text-[var(--color-text-faint)]">
            Real regulatory context (not investment or tax advice): India has kept a flat 30% tax on virtual
            digital asset gains plus 1% TDS on transaction value since 2022, unchanged through the 2026 budget;
            no comprehensive crypto law or regulator exists yet.
          </p>
        )}
        {(data.asset_class === 'real_assets' || data.asset_class === 'alternatives') && (
          <p className="max-w-3xl text-[11px] text-[var(--color-text-faint)]">
            True private {data.asset_class === 'real_assets' ? 'real estate/infrastructure' : 'hedge-fund/private-equity'}{' '}
            data isn't available free anywhere. These are real, liquid, publicly-traded proxies, not the private
            market itself.
          </p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {sorted.map((row) => (
          <TailRiskCard key={row.ticker} row={row} isFixedIncome={isFixedIncome} />
        ))}
      </div>
    </div>
  )
}
