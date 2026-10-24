import type { MarginSurvivalRow, UfcMarginSurvivalRow } from '../lib/types'
import { pct } from '../lib/format'

const RISK_LABEL_COLOR: Record<string, string> = {
  'ELITE SURVIVAL': 'var(--color-positive)',
  'VERY STRONG': 'var(--color-positive)',
  STRONG: 'var(--color-accent)',
  MODERATE: 'var(--color-accent)',
  'HIGH BLOWOUT RISK': '#e05252',
}

// Win/draw and lose-by-(threshold-1) both leave the +threshold line
// covered, so they're shown as one merged "survive comfortably" segment
// -- the push (lose by exactly threshold) and fail (lose by more than
// threshold) segments are what actually separates a +threshold pick
// from a normal moneyline/spread pick, so those stay visually distinct.
// Soccer/UEFA (`lose_1_prob` present) buckets by discrete goal margin;
// NFL/NBA (no discrete goal-margin concept -- a continuous points
// margin instead, see compute_margin_survival_team_sport.py) falls
// back to the same real p_cover/p_push/p_fail every row already
// carries, labeled at this row's own real threshold.
export function MarginBar({ row }: { row: MarginSurvivalRow | UfcMarginSurvivalRow }) {
  const t = row.threshold
  const hasDiscreteBuckets = 'lose_1_prob' in row && row.lose_1_prob !== null && row.lose_1_prob !== undefined
  const segments =
    t === null
      ? // UFC's real binary shape -- no real "push" state exists for a
        // finish/no-finish outcome (see fight_distance_model.py), so
        // just two segments: survive to a real decision, or get
        // finished first.
        [
          { key: 'cover', value: row.p_cover, color: 'var(--color-positive)', label: `Survive to decision ${pct(row.p_cover)}` },
          { key: 'fail', value: row.p_fail, color: '#e05252', label: `Finished ${pct(row.p_fail)}` },
        ]
      : hasDiscreteBuckets
        ? (() => {
            const r = row as MarginSurvivalRow
            const winDraw = r.win_prob + r.draw_prob
            return [
              { key: 'wd', value: winDraw, color: 'var(--color-positive)', label: `Win/Draw ${pct(winDraw)}` },
              { key: 'l1', value: r.lose_1_prob, color: 'var(--color-accent)', label: `Lose by ${t - 1} ${pct(r.lose_1_prob)}` },
              { key: 'l2', value: r.lose_2_prob, color: '#d9a441', label: `Lose by ${t} (push) ${pct(r.lose_2_prob)}` },
              { key: 'l3p', value: r.lose_3_prob + r.lose_4plus_prob, color: '#e05252', label: `Lose by ${t + 1}+ ${pct(r.lose_3_prob + r.lose_4plus_prob)}` },
            ]
          })()
        : [
            { key: 'cover', value: row.p_cover, color: 'var(--color-positive)', label: `Cover ${pct(row.p_cover)}` },
            { key: 'push', value: row.p_push, color: '#d9a441', label: `Push (lose by ${t}) ${pct(row.p_push)}` },
            { key: 'fail', value: row.p_fail, color: '#e05252', label: `Lose by ${t + 1}+ ${pct(row.p_fail)}` },
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

const VERDICT_STYLE = {
  pick: { bg: 'var(--color-positive)', fg: '#0b1410' },
  lean: { bg: 'var(--color-accent)', fg: '#241a05' },
  pass: { bg: 'var(--color-panel)', fg: 'var(--color-text-faint)' },
}

// Synthesizes risk_label + value_gap into one explicit call -- risk
// gates first (a High Blowout Risk team is never a Pick even at a
// generous price), price only breaks ties within an acceptable risk
// tier. See compute_margin_survival.py's verdict() for the exact rule;
// this component only renders what the backend already decided.
// Matched by TIER prefix, not the exact string -- "PICK +2" (soccer),
// "PICK +14" (NFL), "PICK +20" (NBA) and "PICK DISTANCE" (UFC) are all
// the same tier, just at each league's own real tag.
export function VerdictPill({ verdict }: { verdict: string }) {
  const style = verdict.startsWith('PICK ') ? VERDICT_STYLE.pick : verdict.startsWith('LEAN ') ? VERDICT_STYLE.lean : VERDICT_STYLE.pass
  return (
    <span
      className="whitespace-nowrap rounded-sm px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
      style={{ backgroundColor: style.bg, color: style.fg, border: verdict === 'PASS' ? '1px solid var(--color-border)' : undefined }}
    >
      {verdict}
    </span>
  )
}
