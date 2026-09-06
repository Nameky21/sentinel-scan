import { Fragment, useMemo, useState } from 'react'

import type { Finding, Risk } from '../api/types'
import { RISK_ORDER } from '../api/types'
import { SeverityBadge } from './SeverityBadge'

interface Issue {
  name: string
  risk: Risk
  confidence: string
  description: string | null
  remediation: string
  remediation_is_curated: boolean
  cwe_id: string | null
  plugin_id: string | null
  reference: string | null
  instances: { url: string | null; param: string | null; evidence: string | null }[]
}

function groupFindings(findings: Finding[]): Issue[] {
  const byName = new Map<string, Issue>()
  for (const finding of findings) {
    const existing = byName.get(finding.name)
    const instance = { url: finding.affected_url, param: finding.param, evidence: finding.evidence }
    if (existing) {
      existing.instances.push(instance)
    } else {
      byName.set(finding.name, { ...finding, instances: [instance] })
    }
  }
  return [...byName.values()].sort(
    (a, b) => RISK_ORDER.indexOf(a.risk) - RISK_ORDER.indexOf(b.risk) || a.name.localeCompare(b.name),
  )
}

export function FindingsTable({ findings }: { findings: Finding[] }) {
  const [riskFilter, setRiskFilter] = useState<Risk | 'All'>('All')
  const [expanded, setExpanded] = useState<string | null>(null)

  const issues = useMemo(() => groupFindings(findings), [findings])
  const visible = riskFilter === 'All' ? issues : issues.filter((issue) => issue.risk === riskFilter)

  const counts = useMemo(() => {
    const map = new Map<Risk, number>()
    for (const issue of issues) map.set(issue.risk, (map.get(issue.risk) ?? 0) + 1)
    return map
  }, [issues])

  if (findings.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center text-sm text-slate-400">
        No findings were reported for this scan.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(['All', ...RISK_ORDER] as const).map((risk) => {
          const count = risk === 'All' ? issues.length : (counts.get(risk) ?? 0)
          const active = riskFilter === risk
          return (
            <button
              key={risk}
              type="button"
              onClick={() => setRiskFilter(risk)}
              disabled={count === 0}
              className={`rounded-full px-3 py-1 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${
                active ? 'bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/40' : 'bg-slate-800/70 text-slate-400 hover:text-slate-200'
              }`}
            >
              {risk} · {count}
            </button>
          )
        })}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Severity</th>
              <th className="px-4 py-3 font-medium">Finding</th>
              <th className="px-4 py-3 font-medium">Confidence</th>
              <th className="px-4 py-3 font-medium text-right">Locations</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-900/30">
            {visible.map((issue) => {
              const open = expanded === issue.name
              return (
                <Fragment key={issue.name}>
                  <tr
                    onClick={() => setExpanded(open ? null : issue.name)}
                    className="cursor-pointer transition hover:bg-slate-800/40"
                  >
                    <td className="px-4 py-3">
                      <SeverityBadge risk={issue.risk} />
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-100">
                      {issue.name}
                      {issue.cwe_id && <span className="ml-2 text-xs text-slate-500">CWE-{issue.cwe_id}</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{issue.confidence}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-400">{issue.instances.length}</td>
                  </tr>
                  {open && (
                    <tr className="bg-slate-950/60">
                      <td colSpan={4} className="space-y-4 px-4 py-4 text-sm">
                        {issue.description && (
                          <div>
                            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                              Description
                            </p>
                            <p className="text-slate-300">{issue.description}</p>
                          </div>
                        )}
                        <div>
                          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                            Remediation
                            {issue.remediation_is_curated && (
                              <span className="ml-2 normal-case tracking-normal text-teal-400">
                                SentinelScan guidance
                              </span>
                            )}
                          </p>
                          <p className="text-slate-300">{issue.remediation}</p>
                        </div>
                        <div>
                          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                            Affected locations
                          </p>
                          <ul className="space-y-1 font-mono text-xs text-slate-400">
                            {issue.instances.slice(0, 10).map((instance, index) => (
                              <li key={index} className="break-all">
                                {instance.url}
                                {instance.param && <span className="text-slate-500"> (param: {instance.param})</span>}
                              </li>
                            ))}
                            {issue.instances.length > 10 && (
                              <li className="font-sans text-slate-500">
                                …and {issue.instances.length - 10} more
                              </li>
                            )}
                          </ul>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
