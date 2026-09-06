import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

import { api } from '../api/client'
import type { ZapStatus } from '../api/types'

export function NavBar() {
  const [zap, setZap] = useState<ZapStatus | null>(null)

  useEffect(() => {
    const check = () => api.zapStatus().then(setZap).catch(() => setZap({ connected: false }))
    check()
    const timer = window.setInterval(check, 15000)
    return () => window.clearInterval(timer)
  }, [])

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm font-medium transition ${
      isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-100'
    }`

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
        <NavLink to="/" className="flex items-center gap-2 text-base font-semibold tracking-tight">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-teal-500/15 text-teal-400">
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden>
              <path
                fillRule="evenodd"
                d="M9.661 2.237a.531.531 0 0 1 .678 0 11.947 11.947 0 0 0 7.078 2.749.5.5 0 0 1 .479.425c.069.52.104 1.05.104 1.59 0 5.162-3.26 9.563-7.834 11.256a.48.48 0 0 1-.332 0C5.26 16.564 2 12.163 2 7c0-.538.035-1.069.104-1.589a.5.5 0 0 1 .48-.425 11.947 11.947 0 0 0 7.077-2.75Z"
                clipRule="evenodd"
              />
            </svg>
          </span>
          SentinelScan
        </NavLink>

        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            New scan
          </NavLink>
          <NavLink to="/history" className={linkClass}>
            History
          </NavLink>
        </nav>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className={`h-2 w-2 rounded-full ${zap?.connected ? 'bg-emerald-400' : 'bg-red-500'}`} />
          <span className="text-slate-400">
            {zap?.connected ? `ZAP ${zap.version} connected` : 'ZAP disconnected'}
          </span>
        </div>
      </div>
    </header>
  )
}
