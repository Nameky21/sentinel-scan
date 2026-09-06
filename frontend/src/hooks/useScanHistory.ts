import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Scan } from '../api/types'

export function useScanHistory() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setScans(await api.listScans())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan history')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { scans, loading, error, reload: load }
}
