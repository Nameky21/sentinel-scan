import type {
  DeleteAllScansResponse,
  Finding,
  Report,
  ReportFormat,
  Risk,
  Scan,
  ScanStatusResponse,
  ZapStatus,
} from './types'

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(detail?.detail ?? `Request failed (${response.status})`)
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

export const api = {
  zapStatus: () => request<ZapStatus>('/api/zap/status'),

  listScans: () => request<Scan[]>('/api/scans'),

  getScan: (id: number) => request<Scan>(`/api/scans/${id}`),

  getScanStatus: (id: number) => request<ScanStatusResponse>(`/api/scans/${id}/status`),

  deleteScan: (id: number) => request<void>(`/api/scans/${id}`, { method: 'DELETE' }),

  deleteAllScans: () => request<DeleteAllScansResponse>('/api/scans', { method: 'DELETE' }),

  startScan: (body: { target_url: string; authorization_confirmed: boolean; authorized_by?: string }) =>
    request<Scan>('/api/scans', { method: 'POST', body: JSON.stringify(body) }),

  listFindings: (id: number, risk?: Risk) =>
    request<Finding[]>(`/api/scans/${id}/findings${risk ? `?risk=${encodeURIComponent(risk)}` : ''}`),

  generateReport: (id: number, format: ReportFormat) =>
    request<Report>(`/api/scans/${id}/report?format=${format}`, { method: 'POST' }),

  reportUrl: (id: number, format: ReportFormat) => `${API_BASE}/api/scans/${id}/report/${format}`,
}
