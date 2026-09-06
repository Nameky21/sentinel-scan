import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../api/client'
import { AuthorizationGate } from '../components/AuthorizationGate'

export function NewScanPage() {
  const navigate = useNavigate()
  const [targetUrl, setTargetUrl] = useState('http://localhost:3000')
  const [confirmed, setConfirmed] = useState(false)
  const [authorizedBy, setAuthorizedBy] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const scan = await api.startScan({
        target_url: targetUrl.trim(),
        authorization_confirmed: confirmed,
        authorized_by: authorizedBy.trim() || undefined,
      })
      navigate(`/scans/${scan.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scan')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New scan</h1>
        <p className="mt-1 text-sm text-slate-400">
          Crawls the target with ZAP's spider and browser-driven AJAX spider, then runs an active scan and
          collects the findings.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-5">
        <div>
          <label htmlFor="target" className="mb-1.5 block text-sm font-medium text-slate-300">
            Target URL
          </label>
          <input
            id="target"
            type="url"
            required
            value={targetUrl}
            onChange={(event) => setTargetUrl(event.target.value)}
            placeholder="https://example.com"
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2.5 font-mono text-sm text-slate-100 placeholder:text-slate-600 focus:border-teal-500 focus:outline-none"
          />
        </div>

        <AuthorizationGate
          confirmed={confirmed}
          onConfirmedChange={setConfirmed}
          authorizedBy={authorizedBy}
          onAuthorizedByChange={setAuthorizedBy}
        />

        {error && (
          <p className="rounded-md border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-300">{error}</p>
        )}

        <button
          type="submit"
          disabled={!confirmed || submitting}
          className="w-full rounded-md bg-teal-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
        >
          {submitting ? 'Starting scan…' : 'Start scan'}
        </button>
      </form>
    </div>
  )
}
