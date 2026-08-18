export function PageState({ loading, error }: { loading: boolean; error: string | null }) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 text-center text-[12px] text-[var(--color-text-faint)]">
      {loading ? 'Loading...' : `Failed to load: ${error}`}
    </div>
  )
}
