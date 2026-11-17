// Thin wrapper around the Alertr API. In dev, Vite proxies /api to FastAPI.
const BASE = '/api'

export type Health = { status: string; documents: number }

async function get<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const getHealth = () => get<Health>('/health')
