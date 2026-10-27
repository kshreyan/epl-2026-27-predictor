import { lazy, Suspense } from 'react'
import { HashRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
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
  // "swiss" (UCL/UEL/UECL's 36-team partial-schedule league phase) has
  // no table/races tab to land on -- an unknown sub-path goes to
  // Fixtures instead of a route that would 404 its data. Defaults to
  // "table" while the manifest is still loading (every league,
  // whatever its format, matched it correctly once -- a brief flash
  // at worst).
  const defaultTab = format === 'swiss' ? 'fixtures' : 'table'
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
            <Route path="*" element={<Navigate to={`/${leagueId}/${defaultTab}`} replace />} />
          </Routes>
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
        <Route path="/:leagueId/*" element={<LeagueRoutes />} />
      </Routes>
    </HashRouter>
  )
}
