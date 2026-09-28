import type { MarginSurvivalRow } from '../lib/types'
import { pct } from '../lib/format'

const RISK_LABEL_COLOR: Record<string, string> = {
  'ELITE +2 SURVIVAL': 'var(--color-positive)',
  'VERY STRONG': 'var(--color-positive)',
  STRONG: 'var(--color-accent)',
  MODERATE: 'var(--color-accent)',
  'HIGH BLOWOUT RISK': '#e05252',
}

// Win/draw and lose-by-1 both leave the +2.0 line covered, so they're
// shown as one merged "survive comfortably" segment -- the push (lose-2)
// and fail (lose-3+) segments are what actually separates a +2 pick from
// a normal moneyline/spread pick, so those stay visually distinct.
export function MarginBar({ row }: { row: MarginSurvivalRow }) {
  const winDraw = row.win_prob + row.draw_prob
  const segments = [
    { key: 'wd', value: winDraw, color: 'var(--color-positive)', label: `Win/Draw ${pct(winDraw)}` },
    { key: 'l1', value: row.lose_1_prob, color: 'var(--color-accent)', label: `Lose by 1 ${pct(row.lose_1_prob)}` },
    { key: 'l2', value: row.lose_2_prob, color: '#d9a441', label: `Lose by 2 (push) ${pct(row.lose_2_prob)}` },
    { key: 'l3p', value: row.lose_3_prob + row.lose_4plus_prob, color: '#e05252', label: `Lose by 3+ ${pct(row.lose_3_prob + row.lose_4plus_prob)}` },
  ]
  return (
    <div className="space-y-1">
      <div className="flex h-2.5 w-full overflow-hidden rounded-sm">
        {segments.map((s) => (
          <div key={s.key} style={{ width: `${s.value * 100}%`, backgroundColor: s.color }} title={s.label} />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-[var(--color-text-faint)]">
        {segments.map((s) => (
          <span key={s.key}>{s.label}</span>
        ))}
      </div>
    </div>
  )
}

export function RiskLabelBadge({ label }: { label: string }) {
  return (
    <span
      className="rounded-sm border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide"
      style={{ color: RISK_LABEL_COLOR[label] ?? 'var(--color-text-faint)', borderColor: 'var(--color-border)' }}
    >
      {label}
    </span>
  )
}

const VERDICT_STYLE: Record<string, { bg: string; fg: string }> = {
  'PICK +2': { bg: 'var(--color-positive)', fg: '#0b1410' },
  'LEAN +2': { bg: 'var(--color-accent)', fg: '#241a05' },
  PASS: { bg: 'var(--color-panel)', fg: 'var(--color-text-faint)' },
}

// Synthesizes risk_label + value_gap into one explicit call -- risk
// gates first (a High Blowout Risk team is never a Pick even at a
// generous price), price only breaks ties within an acceptable risk
// tier. See compute_margin_survival.py's verdict() for the exact rule;
// this component only renders what the backend already decided.
export function VerdictPill({ verdict }: { verdict: string }) {
  const style = VERDICT_STYLE[verdict] ?? VERDICT_STYLE.PASS
  return (
    <span
      className="rounded-sm px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
      style={{ backgroundColor: style.bg, color: style.fg, border: verdict === 'PASS' ? '1px solid var(--color-border)' : undefined }}
    >
      {verdict}
    </span>
  )
}
