import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import type { ScorelineEntry } from '../lib/types'

export function ScorelineDistribution({ scorelines }: { scorelines: ScorelineEntry[] }) {
  const top = scorelines.slice(0, 10)
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={top} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-border)" vertical={false} />
        <XAxis
          dataKey="score"
          tick={{ fill: 'var(--color-text-dim)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
        />
        <YAxis
          // Show real precision below 1% (a long-tail scoreline would
          // otherwise round to "0%" on every tick), whole percent at or
          // above it.
          tickFormatter={(v: number) => {
            const pct = v * 100
            return `${pct < 1 ? pct.toFixed(2) : Math.round(pct)}%`
          }}
          tick={{ fill: 'var(--color-text-faint)', fontSize: 10 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
          width={42}
        />
        <Bar dataKey="probability" fill="var(--color-accent)" radius={0} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  )
}
