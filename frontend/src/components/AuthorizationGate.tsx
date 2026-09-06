interface Props {
  confirmed: boolean
  onConfirmedChange: (value: boolean) => void
  authorizedBy: string
  onAuthorizedByChange: (value: string) => void
}

export function AuthorizationGate({
  confirmed,
  onConfirmedChange,
  authorizedBy,
  onAuthorizedByChange,
}: Props) {
  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
      <div className="flex items-start gap-3">
        <svg className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.63-1.516 2.63H3.72c-1.347 0-2.19-1.463-1.516-2.63L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v4a.75.75 0 0 1-1.5 0v-4A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
            clipRule="evenodd"
          />
        </svg>
        <div className="space-y-3 text-sm">
          <div>
            <p className="font-semibold text-amber-200">Authorization required</p>
            <p className="mt-1 text-slate-300">
              An active scan sends real attack traffic and can disrupt the target. Only scan systems you own or
              have explicit written permission to test — unauthorized scanning is illegal in most jurisdictions.
            </p>
          </div>

          <label className="flex cursor-pointer items-start gap-2.5">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(event) => onConfirmedChange(event.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-slate-600 bg-slate-800 accent-teal-500"
            />
            <span className="text-slate-200">
              I own this target or have explicit written authorization to test it.
            </span>
          </label>

          <div>
            <label htmlFor="authorized-by" className="mb-1 block text-xs font-medium text-slate-400">
              Authorization note (optional — stored with the scan record)
            </label>
            <input
              id="authorized-by"
              type="text"
              value={authorizedBy}
              onChange={(event) => onAuthorizedByChange(event.target.value)}
              placeholder="e.g. Local OWASP Juice Shop container, or engagement/ticket reference"
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-teal-500 focus:outline-none"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
