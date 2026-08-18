import { NavLink } from 'react-router-dom'
import { formatGeneratedAt } from '../lib/format'

const NAV = [
  { to: '/table', label: 'Table' },
  { to: '/races', label: 'Races' },
  { to: '/fixtures', label: 'Fixtures' },
  { to: '/performance', label: 'Model' },
]

export function Header({ modelVersion, generatedAt }: { modelVersion?: string; generatedAt?: string }) {
  return (
    <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-bg)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-2.5">
        <span className="text-[13px] font-semibold tracking-tight text-[var(--color-text)]">
          EPL <span className="text-[var(--color-accent)]">2026-27</span>
        </span>
        <nav className="flex gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
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
