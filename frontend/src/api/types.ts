export type ScanStatus =
  | 'pending'
  | 'spidering'
  | 'active_scanning'
  | 'completed'
  | 'failed'

export type Risk = 'High' | 'Medium' | 'Low' | 'Informational'
export type Confidence = 'Confirmed' | 'High' | 'Medium' | 'Low'
export type ReportFormat = 'html' | 'pdf'

export interface Scan {
  id: number
  target_url: string
  status: ScanStatus
  authorization_confirmed: boolean
  authorized_by: string | null
  progress_percent: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  findings_by_risk?: Record<string, number>
  findings_total?: number
}

export interface ScanStatusResponse {
  id: number
  status: ScanStatus
  progress_percent: number
  error_message: string | null
}

export interface Finding {
  id: number
  scan_id: number
  plugin_id: string | null
  name: string
  risk: Risk
  confidence: Confidence
  description: string | null
  solution: string | null
  reference: string | null
  affected_url: string | null
  param: string | null
  attack: string | null
  evidence: string | null
  cwe_id: string | null
  wasc_id: string | null
  remediation: string
  remediation_is_curated: boolean
}

export interface ZapStatus {
  connected: boolean
  version?: string
  error?: string
}

export interface Report {
  id: number
  scan_id: number
  format: ReportFormat
  generated_at: string
  download_url: string
}

export const RISK_ORDER: Risk[] = ['High', 'Medium', 'Low', 'Informational']
