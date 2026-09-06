import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { ScanStatusResponse } from '../api/types'

const POLL_INTERVAL_MS = 2000
const TERMINAL = ['completed', 'failed']

export function useScanStatus(scanId: number | null) {
  const [status, setStatus] = useState<ScanStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (scanId === null) return
    let cancelled = false
    let timer: number

    const poll = async () => {
      try {
        const next = await api.getScanStatus(scanId)
        if (cancelled) return
        setStatus(next)
        setError(null)
        if (!TERMINAL.includes(next.status)) {
          timer = window.setTimeout(poll, POLL_INTERVAL_MS)
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load scan status')
        timer = window.setTimeout(poll, POLL_INTERVAL_MS)
      }
    }

    poll()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [scanId])

  return { status, error, isRunning: status !== null && !TERMINAL.includes(status.status) }
}
