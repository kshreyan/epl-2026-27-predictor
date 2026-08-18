import type { PositionDistributionRow } from './types'

export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return `${(x * 100).toFixed(digits)}%`
}

export function num(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return x.toFixed(digits)
}

export function getFinishProbability(row: PositionDistributionRow, position: number): number {
  const v = row[`finish_${position}_probability`]
  return typeof v === 'number' ? v : 0
}

export function formatKickoff(iso: string): string {
  // Real match kickoff times are meaningful in UK stadium local time, not
  // whatever timezone happens to be set on the viewer's device -- without
  // an explicit timeZone here, the same match would show a different hour
  // to viewers in different timezones, which is simply wrong for a factual
  // kickoff time.
  const d = new Date(iso)
  const formatted = d.toLocaleString('en-GB', {
    weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    timeZone: 'Europe/London',
  })
  return `${formatted} UK`
}

export function formatGeneratedAt(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-GB', {
    year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
  }) + ' UTC'
}
