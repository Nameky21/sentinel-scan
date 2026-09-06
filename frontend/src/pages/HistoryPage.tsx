import { Link } from 'react-router-dom'

import type { Risk, Scan } from '../api/types'
import { RISK_ORDER } from '../api/types'
import { SeverityBadge } from '../components/SeverityBadge'
import { useScanHistory } from '../hooks/useScanHistory'

const STATUS_STYLES: Record<string, string> = {
  completed: 'text-emerald-400',
  failed: 'text-red-400',
  pending: 'text-slate-400',
  spidering: 'text-teal-400',
  active_scanning: 'text-teal-400',
}

function RiskCounts({ scan }: { scan: Scan }) {
  const counts = scan.findings_by_risk ?? {}
  const present = RISK_ORDER.filter((risk) => (counts[risk] ?? 0) > 0)
  if (present.length === 0) return <span className="text-xs text-slate-600">—</span>
  return (
    <div className="flex flex-wrap gap-1.5">
      {present.map((risk) => (
        <span key={risk} className="flex items-center gap-1">
          <SeverityBadge risk={risk as Risk} />
          <span className="text-xs tabular-nums text-slate-400">{counts[risk]}</span>
        </span>
      ))}
    </div>
  )
}

export function HistoryPage() {
  const { scans, loading, error } = useScanHistory()

  if (loading) return <p className="text-sm text-slate-400">Loading scan history…</p>
  if (error) return <p className="text-sm text-red-300">{error}</p>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Scan history</h1>
        <p className="mt-1 text-sm text-slate-400">{scans.length} scan{scans.length === 1 ? '' : 's'} recorded</p>
      </div>

      {scans.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center text-sm text-slate-400">
          No scans yet. <Link to="/" className="text-teal-400 hover:underline">Start one</Link>.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Target</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Findings</th>
                <th className="px-4 py-3 font-medium">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/30">
              {scans.map((scan) => (
                <tr key={scan.id} className="transition hover:bg-slate-800/40">
                  <td className="px-4 py-3">
                    <Link to={`/scans/${scan.id}`} className="font-mono text-slate-200 hover:text-teal-400">
                      {scan.target_url}
                    </Link>
                  </td>
                  <td className={`px-4 py-3 ${STATUS_STYLES[scan.status] ?? 'text-slate-400'}`}>
                    {scan.status.replace('_', ' ')}
                    {scan.status !== 'completed' && scan.status !== 'failed' && ` · ${scan.progress_percent}%`}
                  </td>
                  <td className="px-4 py-3">
                    <RiskCounts scan={scan} />
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {scan.started_at ? new Date(scan.started_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
