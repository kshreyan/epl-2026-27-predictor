import { NavLink, useLocation } from 'react-router-dom'
import { formatGeneratedAt } from '../lib/format'
import { useDashboardJson } from '../lib/useDashboardData'

interface LeagueEntry { league_id: string; display_name: string; country: string; format: 'single_table' | 'groups' }
interface LeaguesManifest { leagues: LeagueEntry[] }

// A "groups" competition (UEFA Nations League) has no combined table --
// no Table/Races/Fixtures/Model tabs for it to point at, just its own
// International Break section (predictions + its weekly trusted picks)
// and the site-wide Trusted Picks page (which now also surfaces
// international picks). single_table leagues get the full tab set,
// including a link over to International Break.
const SINGLE_TABLE_NAV = [
  { to: 'table', label: 'Table' },
  { to: 'races', label: 'Races' },
  { to: 'fixtures', label: 'Fixtures' },
  { to: 'performance', label: 'Model' },
  { to: 'trusted-picks', label: 'Trusted Picks' },
  { to: 'international', label: 'International Break' },
]
const GROUPS_NAV = [
  { to: 'international', label: 'International Break' },
  { to: 'trusted-picks', label: 'Trusted Picks' },
]
const GROUPS_ONLY_TABS = new Set(['table', 'races', 'fixtures', 'performance'])

function LeagueSwitcher({ leagueId, leagues }: { leagueId: string; leagues: LeagueEntry[] }) {
  const location = useLocation()
  // Preserve the current tab (table/races/fixtures/performance/trusted-
  // picks/international) when switching competitions, e.g.
  // /epl/fixtures -> /la_liga/fixtures -- except a tab that doesn't
  // exist for the target league's format (e.g. staying on "fixtures"
  // when switching to the "groups"-format Nations League), which falls
  // back to that format's own default tab instead of a dead route.
  const currentTab = location.pathname.split('/')[2] || 'table'
  if (leagues.length <= 1) return null
  return (
    <select
      value={leagueId}
      onChange={(e) => {
        const target = leagues.find((l) => l.league_id === e.target.value)
        const tab = target?.format === 'groups' && GROUPS_ONLY_TABS.has(currentTab) ? 'international' : currentTab
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
  const nav = current?.format === 'groups' ? GROUPS_NAV : SINGLE_TABLE_NAV

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
