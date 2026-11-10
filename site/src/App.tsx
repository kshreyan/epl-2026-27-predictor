import { lazy, Suspense } from 'react'
import { HashRouter, NavLink, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { useDashboardJson } from './lib/useDashboardData'
import type { Envelope, MatchPredictionRow } from './lib/types'

// Route-level code splitting: Recharts (used on every page) pushes a
// single-bundle build over Vite's 500kB warning threshold, so each page
// (and its chart imports) loads on demand instead.
const ExpectedTablePage = lazy(() => import('./pages/ExpectedTablePage').then((m) => ({ default: m.ExpectedTablePage })))
const RacesPage = lazy(() => import('./pages/RacesPage').then((m) => ({ default: m.RacesPage })))
const FixturesPage = lazy(() => import('./pages/FixturesPage').then((m) => ({ default: m.FixturesPage })))
const ModelPerformancePage = lazy(() =>
  import('./pages/ModelPerformancePage').then((m) => ({ default: m.ModelPerformancePage })),
)
const Plus2BoardPage = lazy(() => import('./pages/Plus2BoardPage').then((m) => ({ default: m.Plus2BoardPage })))
const KnockoutPage = lazy(() => import('./pages/KnockoutPage').then((m) => ({ default: m.KnockoutPage })))
const StandingsPage = lazy(() => import('./pages/StandingsPage').then((m) => ({ default: m.StandingsPage })))
const MarketTailRiskPage = lazy(() =>
  import('./pages/MarketTailRiskPage').then((m) => ({ default: m.MarketTailRiskPage })),
)

// Every page reads its own leagueId from the route param and builds its
// dashboard-JSON filename as `${leagueId}_<name>.json` -- one component
// per view, not duplicated per competition. "epl" produces exactly the
// filenames this site always had, so this is a route-shape change only,
// not a data change, for the competition that was already live.
function HeaderData({ leagueId }: { leagueId: string }) {
  // match_predictions.json exists for every league regardless of
  // format (unlike expected_table.json, which a "swiss"-format league
  // never produces -- see LeagueConfig.format).
  const { data } = useDashboardJson<Envelope<MatchPredictionRow>>(`${leagueId}_match_predictions.json`)
  return <Header modelVersion={data?.model_version} generatedAt={data?.generated_at} leagueId={leagueId} />
}

function LeagueRoutes() {
  const { leagueId = 'epl' } = useParams<{ leagueId: string }>()
  const { data: manifest } = useDashboardJson<{ leagues: { league_id: string; format: string }[] }>('leagues.json')
  const format = manifest?.leagues.find((l) => l.league_id === leagueId)?.format
  // "swiss" (UCL/UEL/UECL's 36-team partial-schedule league phase),
  // "points" (NFL/NBA/NCAA Football, a real conference/division-
  // seeded sport, not a goal-difference table), and "groups" (UEFA
  // Nations League's real 54-team group-stage field, no combined
  // table either) all have no table/races tab to land on -- an
  // unknown sub-path for any of them goes to Fixtures instead of a
  // route that would 404 its data. Defaults to "table" while the
  // manifest is still loading (every league, whatever its format,
  // matched it correctly once -- a brief flash at worst).
  const defaultTab = format === 'swiss' || format === 'points' || format === 'groups' ? 'fixtures' : 'table'
  return (
    <div className="flex min-h-screen flex-col">
      <HeaderData leagueId={leagueId} />
      <main className="flex-1">
        <Suspense fallback={<div className="px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">Loading...</div>}>
          <Routes>
            <Route path="table" element={<ExpectedTablePage leagueId={leagueId} />} />
            <Route path="races" element={<RacesPage leagueId={leagueId} />} />
            <Route path="fixtures" element={<FixturesPage leagueId={leagueId} />} />
            <Route path="performance" element={<ModelPerformancePage leagueId={leagueId} />} />
            {/* Cross-league: the +2 board spans every covered competition,
                not just the current leagueId. */}
            <Route path="plus2" element={<Plus2BoardPage />} />
            {/* "swiss"-format leagues only (UCL/UEL/UECL) -- see
                simulate_continental_cup_knockout.py. */}
            <Route path="knockout" element={<KnockoutPage leagueId={leagueId} />} />
            {/* "points"-format leagues only (NFL/NBA/NCAA Football)
                -- see simulate_team_sport_season.py. */}
            <Route path="standings" element={<StandingsPage leagueId={leagueId} />} />
            <Route path="*" element={<Navigate to={`/${leagueId}/${defaultTab}`} replace />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}

// Markets side: a real instrument's own tail-risk read, not a two-team
// matchup -- a deliberately separate, minimal route namespace from
// `/:leagueId/*` rather than forcing it through the sports
// LeagueSwitcher/table-races-fixtures nav shape it doesn't fit.
interface MarketEntry { market_id: string; display_name: string; country: string; asset_class: string }
interface MarketsManifest { markets: MarketEntry[] }

// Two real country groups (USA Assets / India Assets), each listing
// its own real asset classes -- reads config/markets.yaml's real
// scope directly via markets.json, never hardcodes which asset
// classes exist for which country (the 3 India gaps -- commodities,
// fixed income & credit, alternatives -- are simply absent from the
// real manifest, not greyed out or faked).
function MarketSwitcher({ marketId, markets }: { marketId: string; markets: MarketEntry[] }) {
  if (markets.length === 0) return null
  const byCountry = new Map<string, MarketEntry[]>()
  for (const m of markets) {
    const list = byCountry.get(m.country) ?? []
    list.push(m)
    byCountry.set(m.country, list)
  }
  return (
    <select
      value={marketId}
      onChange={(e) => {
        window.location.hash = `#/markets/${e.target.value}`
      }}
      className="tnum rounded border border-[var(--color-border)] bg-[var(--color-panel)] px-2 py-1 text-[12px] text-[var(--color-text)]"
    >
      {[...byCountry.entries()].map(([country, group]) => (
        <optgroup key={country} label={`${country} Assets`}>
          {group.map((m) => (
            <option key={m.market_id} value={m.market_id}>
              {m.display_name}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}

function MarketsRoutes() {
  const { marketId = 'us_equities' } = useParams<{ marketId: string }>()
  const { data: manifest } = useDashboardJson<MarketsManifest>('markets.json')
  const markets = manifest?.markets ?? []
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-bg)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-2.5">
          <span className="text-[13px] font-semibold tracking-tight text-[var(--color-text)]">
            Markets <span className="text-[var(--color-accent)]">2026</span>
          </span>
          <MarketSwitcher marketId={marketId} markets={markets} />
          <NavLink to="/epl/table" className="ml-auto text-[12px] text-[var(--color-text-dim)] hover:text-[var(--color-text)]">
            &larr; Back to soccer/sports predictor
          </NavLink>
        </div>
      </header>
      <main className="flex-1">
        <Suspense fallback={<div className="px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">Loading...</div>}>
          <MarketTailRiskPage marketId={marketId} />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/epl/table" replace />} />
        <Route path="/markets/:marketId" element={<MarketsRoutes />} />
        <Route path="/:leagueId/*" element={<LeagueRoutes />} />
      </Routes>
    </HashRouter>
  )
}
