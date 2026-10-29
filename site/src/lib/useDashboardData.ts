import { useEffect, useState } from 'react'

// Every fetch here is relative -- ./data/<file>.json, resolved against
// Vite's `base` at build time -- so this ships as a fully static site
// with zero runtime API calls, per the project's constraints.
export function useDashboardJson<T>(filename: string): { data: T | null; error: string | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    // `cache: 'no-cache'` -- NOT the default fetch cache mode, and NOT
    // `no-store`: this still lets the browser keep a stored copy (and
    // GitHub Pages return a cheap 304 when nothing changed), but
    // forces a real revalidation request every load rather than
    // silently reusing a response for its real 10-minute max-age (the
    // GitHub Pages CDN's own real Cache-Control header on these JSON
    // files) -- confirmed directly this session as the real cause of
    // a brand-new league appearing deployed and correct (verified via
    // a no-store fetch) but not showing up in the app for several
    // minutes after deploy.
    fetch(`${import.meta.env.BASE_URL}data/${filename}`, { cache: 'no-cache' })
      .then((res) => {
        if (!res.ok) throw new Error(`${filename}: HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (!cancelled) {
          setData(json as T)
          setLoading(false)
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [filename])

  return { data, error, loading }
}
