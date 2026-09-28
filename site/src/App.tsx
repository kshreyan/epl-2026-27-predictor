import { lazy, Suspense } from 'react'
import { HashRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { useDashboardJson } from './lib/useDashboardData'
import type { Envelope, ExpectedTableRow } from './lib/types'

// Route-level code splitting: Recharts (used on every page) pushes a
// single-bundle build over Vite's 500kB warning threshold, so each page
// (and its chart imports) loads on demand instead.
const ExpectedTablePage = lazy(() => import('./pages/ExpectedTablePage').then((m) => ({ default: m.ExpectedTablePage })))
const RacesPage = lazy(() => import('./pages/RacesPage').then((m) => ({ default: m.RacesPage })))
const FixturesPage = lazy(() => import('./pages/FixturesPage').then((m) => ({ default: m.FixturesPage })))
const ModelPerformancePage = lazy(() =>
  import('./pages/ModelPerformancePage').then((m) => ({ default: m.ModelPerformancePage })),
)
const InternationalBreakPage = lazy(() =>
  import('./pages/InternationalBreakPage').then((m) => ({ default: m.InternationalBreakPage })),
)

// Every page reads its own leagueId from the route param and builds its
// dashboard-JSON filename as `${leagueId}_<name>.json` -- one component
// per view, not duplicated per competition. "epl" produces exactly the
// filenames this site always had, so this is a route-shape change only,
// not a data change, for the competition that was already live.
function HeaderData({ leagueId }: { leagueId: string }) {
  const { data } = useDashboardJson<Envelope<ExpectedTableRow>>(`${leagueId}_expected_table.json`)
  return <Header modelVersion={data?.model_version} generatedAt={data?.generated_at} leagueId={leagueId} />
}

function LeagueRoutes() {
  const { leagueId = 'epl' } = useParams<{ leagueId: string }>()
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
            {/* Cross-league: UEFA Nations League isn't scoped to any one
                domestic competition, so this page takes no leagueId --
                reachable from any competition's tab bar. */}
            <Route path="international" element={<InternationalBreakPage />} />
            {/* nations_league ("groups" format) has no table/races/fixtures/model
                tabs to land on -- an empty or unknown sub-path for it goes to
                International Break instead of a route that would 404 its data.
                Absolute path (leading "/"), not relative -- a relative target
                here resolves against the current *unmatched* location, which
                for a genuinely unknown path (e.g. an old removed route) does
                not fully replace it and loops the URL instead of navigating. */}
            <Route path="*" element={<Navigate to={`/${leagueId}/${leagueId === 'nations_league' ? 'international' : 'table'}`} replace />} />
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
