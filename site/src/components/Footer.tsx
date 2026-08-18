export function Footer() {
  return (
    <footer className="border-t border-[var(--color-border)] px-4 py-4">
      <div className="mx-auto max-w-6xl space-y-1.5 text-[11px] leading-relaxed text-[var(--color-text-faint)]">
        <p>
          Fixture data: <a className="underline decoration-dotted hover:text-[var(--color-text-dim)]" href="https://fixturedownload.com/" target="_blank" rel="noreferrer">fixturedownload.com</a>.
          {' '}Historical match results: <a className="underline decoration-dotted hover:text-[var(--color-text-dim)]" href="https://www.football-data.co.uk/" target="_blank" rel="noreferrer">football-data.co.uk</a>.
        </p>
        <p>
          Every figure on this site is a probabilistic model output, not a guarantee.{' '}
          <strong className="text-[var(--color-text-dim)]">This is not betting advice.</strong>
        </p>
        <p>
          <a
            className="underline decoration-dotted hover:text-[var(--color-text-dim)]"
            href="https://github.com/kshreyan/epl-2026-27-predictor"
            target="_blank"
            rel="noreferrer"
          >
            Source, methodology, and full audit reports
          </a>
        </p>
      </div>
    </footer>
  )
}
