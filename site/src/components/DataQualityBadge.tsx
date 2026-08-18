// Every prediction figure on this site carries one of these -- never a
// bare number with no provenance context, per the project's data-honesty
// discipline (no market/injury/lineup feed is connected yet).
export function DataQualityBadge({
  marketAvailable,
  dataQualityScore,
}: {
  marketAvailable: boolean
  dataQualityScore?: number | null
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
      {marketAvailable ? 'model + market' : 'model-only'}
      {dataQualityScore != null && (
        <span className="tnum text-[var(--color-text-faint)]">· dq {dataQualityScore.toFixed(2)}</span>
      )}
    </span>
  )
}
