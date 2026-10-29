import type { MarginSurvivalRow } from '../lib/types'
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
export function MarginBar({ row }: { row: MarginSurvivalRow }) {
  const t = row.threshold
  const segments =
    row.lose_1_prob !== null && row.lose_1_prob !== undefined
      ? (() => {
          const winDraw = row.win_prob + row.draw_prob
          return [
            { key: 'wd', value: winDraw, color: 'var(--color-positive)', label: `Win/Draw ${pct(winDraw)}` },
            { key: 'l1', value: row.lose_1_prob, color: 'var(--color-accent)', label: `Lose by ${t - 1} ${pct(row.lose_1_prob)}` },
            { key: 'l2', value: row.lose_2_prob, color: '#d9a441', label: `Lose by ${t} (push) ${pct(row.lose_2_prob)}` },
            { key: 'l3p', value: row.lose_3_prob + row.lose_4plus_prob, color: '#e05252', label: `Lose by ${t + 1}+ ${pct(row.lose_3_prob + row.lose_4plus_prob)}` },
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
// "PICK +14" (NFL), and "PICK +20" (NBA) are all the same tier, just
// at each league's own real tag.
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

// Set only on the favored team's own row by _flag_pick_moneyline() in
// build_margin_survival_json.py -- a convergence of risk tier, model
// scoreline, AND real current standings, all at once, not a separate
// model signal of its own. See that function's docstring for the
// exact 4 conditions.
export function PickMoneylineBadge() {
  return (
    <span
      className="whitespace-nowrap rounded-sm px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
      style={{ backgroundColor: 'var(--color-accent)', color: '#241a05' }}
      title="Real ELITE SURVIVAL PICK verdict vs. a HIGH BLOWOUT RISK opponent, a better own predicted scoreline, and a real top-quartile-vs-bottom-quartile gap in the current standings -- all at once."
    >
      Pick Moneyline
    </span>
  )
}
