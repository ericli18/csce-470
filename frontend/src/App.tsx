import { useEffect, useState } from 'react'
import { getHealth, type Health } from './api'

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message))
  }, [])

  return (
    <main>
      <h1>Alertr</h1>
      {error && <p>API error: {error}</p>}
      {!error && !health && <p>Connecting to API…</p>}
      {health && (
        <p>
          API is {health.status}: {health.documents.toLocaleString()} papers indexed.
        </p>
      )}
    </main>
  )
}

export default App
