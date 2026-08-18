import { useDashboardJson } from '../lib/useDashboardData'
import type { Envelope } from '../lib/types'
import { RaceChart } from '../components/RaceChart'
import { PageState } from '../components/PageState'

interface TitleRow { team: string; title_probability: number }
interface Top4Row { team: string; top_4_probability: number }
interface RelegationRow { team: string; relegation_probability: number }

function RacePanel<T>({ title, filename, prob }: { title: string; filename: string; prob: (row: T) => number }) {
  const { data, error, loading } = useDashboardJson<Envelope<T>>(filename)
  if (loading || error || !data) return <PageState loading={loading} error={error} />
  const rows = data.data.map((r) => ({ team: (r as unknown as { team: string }).team, probability: prob(r) }))
  return (
    <section>
      <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">{title}</h2>
      <div className="border border-[var(--color-border)] p-2">
        <RaceChart rows={rows} accentThreshold={0.05} />
      </div>
    </section>
  )
}

export function RacesPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <RacePanel<TitleRow> title="Title race" filename="epl_title_race.json" prob={(r) => r.title_probability} />
      <RacePanel<Top4Row> title="Top-4 race" filename="epl_top4_race.json" prob={(r) => r.top_4_probability} />
      <RacePanel<RelegationRow> title="Relegation race" filename="epl_relegation_race.json" prob={(r) => r.relegation_probability} />
    </div>
  )
}
