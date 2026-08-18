import { Bar, BarChart, CartesianGrid, LabelList, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from 'recharts'

interface PositionBandRow {
  team: string
  position_5th_percentile: number
  position_95th_percentile: number
  median_position: number
}

// A "floating bar" per team spanning its 5th-95th percentile finishing
// position: an invisible base bar (0 -> p5-1) stacked with a visible one
// (p5-1 -> p95), the idiomatic Recharts pattern for range bars.
export function PositionBand({ rows }: { rows: PositionBandRow[] }) {
  const data = rows.map((r) => {
    const range = r.position_95th_percentile - r.position_5th_percentile
    return {
      team: r.team,
      base: r.position_5th_percentile - 1,
      // A zero-width bar (e.g. a team the model gives ~100% certainty of
      // finishing exactly one position) is real, not a bug -- but fully
      // invisible reads as broken UI, so give it a thin visible sliver.
      range: range === 0 ? 0.15 : range,
      median: r.median_position,
    }
  })
  const height = Math.max(data.length * 22, 120)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 4 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-border)" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 19]}
          ticks={[0, 4, 9, 14, 19]}
          tickFormatter={(v: number) => `${v + 1}`}
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
        <ReferenceLine x={3} stroke="var(--color-border)" strokeDasharray="2 4" /* top-4 line */ />
        <Bar dataKey="base" stackId="band" fill="transparent" />
        <Bar dataKey="range" stackId="band" fill="var(--color-accent-dim)" barSize={10} radius={0}>
          <LabelList
            dataKey="median"
            position="right"
            formatter={(v: unknown) => `med ${v}`}
            style={{ fill: 'var(--color-text-dim)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
