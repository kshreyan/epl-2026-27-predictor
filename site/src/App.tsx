import { lazy, Suspense } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
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

export default function App() {
  // Loaded once here purely for the header's model_version/generated_at --
  // every dashboard JSON file carries the same envelope fields, so any one
  // of them is a valid source for this.
  const { data } = useDashboardJson<Envelope<ExpectedTableRow>>('epl_expected_table.json')

  return (
    <HashRouter>
      <div className="flex min-h-screen flex-col">
        <Header modelVersion={data?.model_version} generatedAt={data?.generated_at} />
        <main className="flex-1">
          <Suspense fallback={<div className="px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">Loading...</div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/table" replace />} />
              <Route path="/table" element={<ExpectedTablePage />} />
              <Route path="/races" element={<RacesPage />} />
              <Route path="/fixtures" element={<FixturesPage />} />
              <Route path="/performance" element={<ModelPerformancePage />} />
            </Routes>
          </Suspense>
        </main>
        <Footer />
      </div>
    </HashRouter>
  )
}
