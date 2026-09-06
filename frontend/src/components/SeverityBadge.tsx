import type { Risk } from '../api/types'

const STYLES: Record<Risk, string> = {
  High: 'bg-risk-high/15 text-risk-high ring-risk-high/30',
  Medium: 'bg-risk-medium/15 text-risk-medium ring-risk-medium/30',
  Low: 'bg-risk-low/15 text-risk-low ring-risk-low/30',
  Informational: 'bg-risk-info/15 text-slate-300 ring-risk-info/30',
}

export function SeverityBadge({ risk }: { risk: Risk }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${STYLES[risk]}`}
    >
      {risk}
    </span>
  )
}
