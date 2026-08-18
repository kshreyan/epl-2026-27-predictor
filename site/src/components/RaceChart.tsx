import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts'

interface RaceChartProps {
  rows: { team: string; probability: number }[]
  accentThreshold?: number // rows at/above this probability get the accent color
}

export function RaceChart({ rows, accentThreshold = 0 }: RaceChartProps) {
  const sorted = [...rows].sort((a, b) => b.probability - a.probability)
  const height = Math.max(sorted.length * 22, 120)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 36, bottom: 4, left: 4 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-border)" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 1]}
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          tick={{ fill: 'var(--color-text-faint)', fontSize: 10 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="team"
          width={140}
          interval={0}
          tick={{ fill: 'var(--color-text)', fontSize: 11 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
        />
        <Bar dataKey="probability" barSize={12} radius={0}>
          {sorted.map((row) => (
            <Cell
              key={row.team}
              fill={row.probability >= accentThreshold ? 'var(--color-accent)' : 'var(--color-border)'}
            />
          ))}
          <LabelList
            dataKey="probability"
            position="right"
            formatter={(v: unknown) => `${(Number(v) * 100).toFixed(1)}%`}
            style={{ fill: 'var(--color-text-dim)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
