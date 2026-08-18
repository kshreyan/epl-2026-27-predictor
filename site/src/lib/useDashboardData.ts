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
    fetch(`${import.meta.env.BASE_URL}data/${filename}`)
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
