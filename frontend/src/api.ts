// Thin wrapper around the Alertr API. In dev, Vite proxies /api to FastAPI.
const BASE = '/api'

export type Health = { status: string; documents: number }

// Mirrors models.Result / models.SearchResponse / models.Alert in src/models.py.
export type Result = {
  pmid: string
  title: string
  date: string // YYYY-MM-DD
  score: number
  pub_types: string[]
  url: string
}

export type SearchResponse = { query: string; total: number; results: Result[] }

export type Alert = { id: number; query: string; created_at: string }

async function get<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const getHealth = () => get<Health>('/health')

export const search = (q: string, opts: { limit?: number; since?: string } = {}) => {
  const params = new URLSearchParams({ q, limit: String(opts.limit ?? 15) })
  if (opts.since) params.set('since', opts.since)
  return get<SearchResponse>(`/search?${params}`)
}
