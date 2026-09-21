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

// MLS has no real relegation and its real playoff field (16 of 30
// teams) is nothing like a European "top 4" Champions League zone --
// simulate_full_season.py already writes the real playoff-cutoff
// probability into this same top_4_probability field for MLS (see
// LeagueConfig.playoff_zone_size), so only the label needs to change
// here; relegation is omitted outright rather than shown as a real-
// looking chart where every bar is truthfully 0%.
const NO_RELEGATION_LEAGUE_IDS = new Set(['mls'])
const TOP4_LABEL_OVERRIDES: Record<string, string> = { mls: 'Playoff race (top 16)' }

export function RacesPage({ leagueId }: { leagueId: string }) {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <RacePanel<TitleRow> title="Title race" filename={`${leagueId}_title_race.json`} prob={(r) => r.title_probability} />
      <RacePanel<Top4Row> title={TOP4_LABEL_OVERRIDES[leagueId] ?? 'Top-4 race'} filename={`${leagueId}_top4_race.json`} prob={(r) => r.top_4_probability} />
      {!NO_RELEGATION_LEAGUE_IDS.has(leagueId) && (
        <RacePanel<RelegationRow> title="Relegation race" filename={`${leagueId}_relegation_race.json`} prob={(r) => r.relegation_probability} />
      )}
    </div>
  )
}
