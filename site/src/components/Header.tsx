import { NavLink, useLocation } from 'react-router-dom'
import { formatGeneratedAt } from '../lib/format'
import { useDashboardJson } from '../lib/useDashboardData'

interface LeagueEntry { league_id: string; display_name: string; country: string; format: 'single_table' | 'swiss' }
interface LeaguesManifest { leagues: LeagueEntry[] }

// "swiss" (UCL/UEL/UECL's 36-team partial-schedule league phase) has
// no goal-difference table/races -- see LeagueConfig.format in
// src/leagues.py.
const SINGLE_TABLE_NAV = [
  { to: 'table', label: 'Table' },
  { to: 'races', label: 'Races' },
  { to: 'fixtures', label: 'Fixtures' },
  { to: 'performance', label: 'Model' },
  { to: 'plus2', label: '+2 Board' },
]
const SWISS_NAV = [
  { to: 'fixtures', label: 'Fixtures' },
  { to: 'knockout', label: 'Knockout' },
  { to: 'performance', label: 'Model' },
  { to: 'plus2', label: '+2 Board' },
]
const NAV_BY_FORMAT: Record<LeagueEntry['format'], typeof SINGLE_TABLE_NAV> = {
  single_table: SINGLE_TABLE_NAV, swiss: SWISS_NAV,
}

function LeagueSwitcher({ leagueId, leagues }: { leagueId: string; leagues: LeagueEntry[] }) {
  const location = useLocation()
  // Preserve the current tab (table/races/fixtures/performance/...)
  // when switching competitions, e.g. /epl/fixtures -> /la_liga/fixtures
  // -- except a tab that doesn't exist for the TARGET league's own
  // real nav (e.g. staying on "table" when switching to a "swiss"-
  // format competition), which falls back to that format's own first
  // real tab instead of a dead route. Checked against the target's own
  // nav list directly, not a hardcoded "only tabs" set, so this stays
  // correct as formats are added.
  const currentTab = location.pathname.split('/')[2] || 'table'
  if (leagues.length <= 1) return null
  return (
    <select
      value={leagueId}
      onChange={(e) => {
        const target = leagues.find((l) => l.league_id === e.target.value)
        const targetNav = NAV_BY_FORMAT[target?.format ?? 'single_table']
        const tabExistsForTarget = targetNav.some((item) => item.to === currentTab)
        const tab = tabExistsForTarget ? currentTab : targetNav[0].to
        window.location.hash = `#/${e.target.value}/${tab}`
      }}
      className="tnum rounded border border-[var(--color-border)] bg-[var(--color-panel)] px-2 py-1 text-[12px] text-[var(--color-text)]"
    >
      {leagues.map((l) => (
        <option key={l.league_id} value={l.league_id}>
          {l.display_name}
        </option>
      ))}
    </select>
  )
}

export function Header({
  modelVersion, generatedAt, leagueId,
}: { modelVersion?: string; generatedAt?: string; leagueId: string }) {
  const { data: manifest } = useDashboardJson<LeaguesManifest>('leagues.json')
  const leagues = manifest?.leagues ?? []
  const current = leagues.find((l) => l.league_id === leagueId)
  const brandName = current ? current.display_name : leagueId.toUpperCase()
  const nav = NAV_BY_FORMAT[current?.format ?? 'single_table']

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-bg)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-2.5">
        <span className="text-[13px] font-semibold tracking-tight text-[var(--color-text)]">
          {brandName} <span className="text-[var(--color-accent)]">2026-27</span>
        </span>
        <LeagueSwitcher leagueId={leagueId} leagues={leagues} />
        <nav className="flex gap-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={`/${leagueId}/${item.to}`}
              className={({ isActive }) =>
                `rounded px-2.5 py-1 text-[12px] transition-colors ${
                  isActive
                    ? 'bg-[var(--color-panel)] text-[var(--color-accent)]'
                    : 'text-[var(--color-text-dim)] hover:text-[var(--color-text)]'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-[11px] text-[var(--color-text-faint)]">
          {modelVersion && <span className="tnum">model {modelVersion}</span>}
          {generatedAt && <span className="tnum">as of {formatGeneratedAt(generatedAt)}</span>}
        </div>
      </div>
    </header>
  )
}
