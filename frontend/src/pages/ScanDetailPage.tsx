import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { api } from '../api/client'
import type { ReportFormat, Scan } from '../api/types'
import { FindingsTable } from '../components/FindingsTable'
import { ScanStatusCard } from '../components/ScanStatusCard'
import { useFindings } from '../hooks/useFindings'
import { useScanStatus } from '../hooks/useScanStatus'

export function ScanDetailPage() {
  const { scanId } = useParams()
  const id = Number(scanId)
  const [scan, setScan] = useState<Scan | null>(null)
  const { status, isRunning } = useScanStatus(Number.isFinite(id) ? id : null)
  const isComplete = status?.status === 'completed'
  const { findings, loading } = useFindings(Number.isFinite(id) ? id : null, isComplete)

  const [generating, setGenerating] = useState<ReportFormat | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)

  useEffect(() => {
    if (!Number.isFinite(id)) return
    api.getScan(id).then(setScan).catch(() => undefined)
  }, [id, isComplete])

  const downloadReport = async (format: ReportFormat) => {
    setGenerating(format)
    setReportError(null)
    try {
      await api.generateReport(id, format)
      window.open(api.reportUrl(id, format), '_blank', 'noopener')
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Failed to generate report')
    } finally {
      setGenerating(null)
    }
  }

  if (!scan || !status) {
    return <p className="text-sm text-slate-400">Loading scan…</p>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Scan #{scan.id}</h1>
          <p className="mt-1 text-sm text-slate-400">
            Authorization: {scan.authorized_by || 'confirmed by operator'}
          </p>
        </div>

        {isComplete && (
          <div className="flex gap-2">
            {(['html', 'pdf'] as const).map((format) => (
              <button
                key={format}
                type="button"
                onClick={() => downloadReport(format)}
                disabled={generating !== null}
                className="rounded-md border border-slate-700 bg-slate-900 px-3.5 py-2 text-sm font-medium text-slate-200 transition hover:border-teal-500/50 hover:text-white disabled:opacity-50"
              >
                {generating === format ? 'Generating…' : `${format.toUpperCase()} report`}
              </button>
            ))}
          </div>
        )}
      </div>

      {reportError && (
        <p className="rounded-md border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-300">{reportError}</p>
      )}

      {(isRunning || status.status === 'failed') && (
        <ScanStatusCard
          status={status.status}
          progress={status.progress_percent}
          targetUrl={scan.target_url}
          error={status.error_message}
        />
      )}

      {isComplete && (
        <>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="font-mono text-sm text-slate-300">{scan.target_url}</p>
            <p className="mt-1 text-xs text-slate-500">
              Completed {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : '—'} ·{' '}
              {scan.findings_total ?? 0} alerts
            </p>
          </div>
          {loading ? <p className="text-sm text-slate-400">Loading findings…</p> : <FindingsTable findings={findings} />}
        </>
      )}
    </div>
  )
}
