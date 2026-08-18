import {
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'
import type { ReliabilityBin } from '../lib/types'

const CLASS_LABEL: Record<string, string> = { home_win: 'Home win', draw: 'Draw', away_win: 'Away win' }
const CLASS_COLOR: Record<string, string> = {
  home_win: 'var(--color-accent)',
  draw: 'var(--color-text-dim)',
  away_win: 'var(--color-positive)',
}

// A reliability curve: mean predicted probability (x) vs. real empirical
// frequency (y) per bin, for each outcome class, against the diagonal
// (perfect calibration) reference line.
export function CalibrationChart({ bins }: { bins: ReliabilityBin[] }) {
  const byClass: Record<string, { x: number; y: number; n: number }[]> = {}
  for (const b of bins) {
    if (b.mean_predicted_probability == null || b.empirical_frequency == null || b.n_matches === 0) continue
    byClass[b.outcome_class] ??= []
    byClass[b.outcome_class].push({ x: b.mean_predicted_probability, y: b.empirical_frequency, n: b.n_matches })
  }
  const diagonal = [
    { x: 0, y: 0 },
    { x: 1, y: 1 },
  ]

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-border)" />
        <XAxis
          type="number"
          dataKey="x"
          domain={[0, 1]}
          name="predicted"
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          tick={{ fill: 'var(--color-text-faint)', fontSize: 10 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
          label={{ value: 'Mean predicted probability', position: 'insideBottom', offset: -4, fill: 'var(--color-text-faint)', fontSize: 10 }}
        />
        <YAxis
          type="number"
          dataKey="y"
          domain={[0, 1]}
          name="empirical"
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          tick={{ fill: 'var(--color-text-faint)', fontSize: 10 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
          label={{ value: 'Empirical frequency', angle: -90, position: 'insideLeft', fill: 'var(--color-text-faint)', fontSize: 10 }}
        />
        <ZAxis type="number" dataKey="n" range={[20, 160]} />
        <Line
          data={diagonal}
          dataKey="y"
          stroke="var(--color-text-faint)"
          strokeDasharray="3 3"
          dot={false}
          legendType="none"
          isAnimationActive={false}
        />
        {Object.entries(byClass).map(([cls, points]) => (
          <Scatter key={cls} name={CLASS_LABEL[cls] ?? cls} data={points} fill={CLASS_COLOR[cls] ?? 'var(--color-accent)'} />
        ))}
        <Legend wrapperStyle={{ fontSize: 11, color: 'var(--color-text-dim)' }} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
