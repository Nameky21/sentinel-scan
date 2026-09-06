import type { ScanStatus } from '../api/types'

const PHASES: { key: ScanStatus; label: string; detail: string }[] = [
  { key: 'pending', label: 'Queued', detail: 'Preparing a fresh ZAP session' },
  { key: 'spidering', label: 'Crawling', detail: 'Mapping the site, including JavaScript-rendered routes' },
  { key: 'active_scanning', label: 'Active scan', detail: 'Probing discovered endpoints for vulnerabilities' },
  { key: 'completed', label: 'Complete', detail: 'Findings collected' },
]

interface Props {
  status: ScanStatus
  progress: number
  targetUrl: string
  error?: string | null
}

export function ScanStatusCard({ status, progress, targetUrl, error }: Props) {
  const failed = status === 'failed'
  const activeIndex = PHASES.findIndex((phase) => phase.key === status)

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">Scanning</p>
          <p className="font-mono text-sm text-slate-200">{targetUrl}</p>
        </div>
        <span className="text-2xl font-semibold tabular-nums">{failed ? '—' : `${progress}%`}</span>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${failed ? 'bg-red-500' : 'bg-teal-500'}`}
          style={{ width: `${failed ? 100 : progress}%` }}
        />
      </div>

      {failed ? (
        <p className="mt-4 rounded-md border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-300">
          Scan failed: {error ?? 'unknown error'}
        </p>
      ) : (
        <ol className="mt-5 space-y-2.5">
          {PHASES.map((phase, index) => {
            const done = activeIndex > index || status === 'completed'
            const current = activeIndex === index && status !== 'completed'
            return (
              <li key={phase.key} className="flex items-start gap-3 text-sm">
                <span
                  className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                    done ? 'bg-teal-400' : current ? 'animate-pulse bg-teal-400' : 'bg-slate-700'
                  }`}
                />
                <span>
                  <span className={done || current ? 'text-slate-200' : 'text-slate-500'}>{phase.label}</span>
                  {current && <span className="ml-2 text-slate-500">{phase.detail}</span>}
                </span>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
