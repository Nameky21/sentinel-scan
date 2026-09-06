import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Finding } from '../api/types'

export function useFindings(scanId: number | null, enabled: boolean) {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (scanId === null || !enabled) return
    setLoading(true)
    try {
      setFindings(await api.listFindings(scanId))
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load findings')
    } finally {
      setLoading(false)
    }
  }, [scanId, enabled])

  useEffect(() => {
    load()
  }, [load])

  return { findings, loading, error, reload: load }
}
