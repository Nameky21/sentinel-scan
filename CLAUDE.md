# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SentinelScan orchestrates OWASP ZAP (a real DAST engine running as a separate daemon) through a crawl and active-scan pipeline, persists findings, and renders them into HTML and PDF reports. The app is the orchestration/persistence/reporting layer — it deliberately does not implement scanning or exploitation itself. Keep that boundary when adding features.

It is also a resume/portfolio project, so commit history, README quality, and documented rationale for trade-offs are part of the deliverable.

## Running things

**Fastest path: `.\scripts\start-all.ps1`.** Starts ZAP, backend, and frontend together (each hidden, logs under `scripts/.run/logs/`), polls `/api/zap/status` until the *backend* confirms it's actually connected to ZAP (not just that ZAP itself is up), then opens the browser. `.\scripts\stop-all.ps1` tears it all down (tree-kills each service so no orphaned child processes are left on the ports). Both are idempotent — safe to re-run if some pieces are already up; they skip anything already listening on its port. `.\scripts\install-shortcuts.ps1` (one-time) creates Desktop shortcuts for both. Prefer this over the manual steps below unless you specifically need to watch live output from one service.

### PowerShell gotchas on this machine (learned the hard way — don't relearn them)

- **`Start-Job` does not survive between separate tool calls.** Each PowerShell/Bash tool invocation is effectively a fresh process; shell state (jobs, variables) doesn't persist across calls. Anything that must outlive the current command (a dev server, a long scan) needs `Start-Process` (a real detached OS process), never `Start-Job`.
- **`Start-Process -Wait` blocks on the whole process tree, not just the direct child.** `scripts/start-zap.ps1` intentionally leaves the ZAP `java.exe` daemon running after it exits — waiting on it with `-Wait` hangs forever. Use `$proc = Start-Process -PassThru; $proc.WaitForExit()` instead.
- **`Start-Process -PassThru` without `-Wait` never populates `.ExitCode`** — it's always `$null`. Judge success by an actual side effect (e.g. the expected port is now listening), not the exit code.
- **`uvicorn --reload` and `npm run dev` (vite) each spawn child processes.** Killing only the top-level PID leaves the real listener orphaned on its port. Use `taskkill /F /T /PID <pid>` (tree-kill), not `Stop-Process`.
- **Vite's dev server can end up bound only to IPv6 (`[::1]:5173`), not `127.0.0.1`.** If `http://127.0.0.1:5173` won't connect but Vite reports it's running, try `http://localhost:5173` instead (or check with `netstat -ano | findstr :5173`).

Python on this machine: bare `python`/`python3` hit the Windows Store alias stub and fail. Use `py -3` to create the venv, and `backend/.venv/Scripts/python.exe` to run anything inside it.

**ZAP daemon must be running before any scan works.** The backend connects to it; `GET /api/zap/status` reports reachability.

```powershell
.\scripts\start-zap.ps1 -ApiKey sentinelscan-dev-key   # key must match backend/.env
```

Do not launch ZAP via its bundled `zap.bat`: it resolves its jar relative to the current working directory, and its 512MB default heap gets the daemon killed by ZAP's own memory watchdog partway through a crawl plus active scan. The script handles both (2GB heap) and waits until the API answers.

```powershell
# Backend (from backend/)
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Tests (from backend/) — pytest.ini sets pythonpath, so no install needed
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m pytest tests/test_report_generator.py::test_writes_a_valid_pdf

# Frontend (from frontend/)
npm run dev            # :5173
npm run build          # tsc -b && vite build
npx tsc -b --noEmit    # typecheck only
```

Scan targets are deliberately-vulnerable practice apps in Docker — never a real third-party site. Juice Shop is the working target for development (`docker run -d -p 3000:3000 --name juice-shop bkimminich/juice-shop`); it is an Angular SPA, which is what makes the AJAX spider phase matter. Other targets are listed in the README.

## Architecture

### Scan lifecycle

`POST /api/scans` validates, inserts a `Scan` row, returns immediately, and hands the id to `scan_orchestrator.run_scan` via FastAPI `BackgroundTasks`. The orchestrator (`backend/app/services/scan_orchestrator.py`) then drives ZAP:

```
new ZAP session → urlopen → spider (0–20%) → AJAX spider (20–44%) → active scan (45–99%) → persist alerts (100%)
```

Two constraints drive that design and are easy to break:

- **Each scan starts a fresh ZAP session.** ZAP accumulates alerts per session, so without this one scan's findings leak into the next.
- **Scans are therefore serialized** by a module-level `threading.Lock`; a concurrent request gets a 409. Any move toward parallel scans needs a different isolation strategy (separate ZAP contexts or daemons), not just removing the lock.

The AJAX spider is a browser-driven crawl (headless Chrome) and is **not optional in practice**: ZAP's traditional spider cannot execute JavaScript, so against a SPA the active scanner sees almost no attack surface. It is wrapped in a non-fatal try/except so a missing browser degrades the scan rather than failing it, and it reports only running/stopped, so its progress is estimated from elapsed time against `AJAX_SPIDER_MAX_DURATION_MINS`.

All three phases are time-boxed via `backend/.env` so runs stay practical; raise the ceilings for thorough assessments.

### Findings and the two places that group them

ZAP emits one alert **per affected URL**, so a single missing header can arrive as 60+ alerts. Both the report generator and the UI group these by alert name into one issue with N locations. That grouping logic currently exists twice — `report_generator.build_report_context` and `FindingsTable.groupFindings` — so a change to grouping semantics needs both.

`severity_mapping.py` keeps ZAP's native four risk tiers rather than inventing a fifth; `RISK_ORDER` is the canonical ordering used for sorting and display in both backend and frontend.

ZAP uses `"-1"` and `"0"` to mean "no CWE/WASC id"; these are normalized to `None` at ingest in the orchestrator, not at render time.

### Remediation knowledge base

`remediation_kb.py` maps ZAP plugin ids to curated remediation text, falling back to ZAP's own `solution` field. It is resolved in **two** call sites — the findings router (for the UI) and the report generator — both via `remediation_for()`, which returns `(text, is_curated)`; the curated flag drives the "SentinelScan guidance" marker. Findings are stored with ZAP's raw `solution`; curated text is resolved at response/render time, never persisted.

### Reports

`build_report_context()` produces one context dict consumed by two **independent** renderers: Jinja2 → self-contained HTML, and ReportLab platypus → natively authored PDF. The PDF is not generated from the HTML; changes to report content usually need to touch both.

Two rendering constraints:
- Jinja2 is configured `autoescape=True` explicitly. `select_autoescape(["html"])` does **not** match the `.html.j2` filename and previously let attacker-influenced finding content render unescaped — there is a regression test for this.
- ReportLab `Paragraph` parses a mini-HTML dialect, so all text passed to it goes through `_esc()`.

Reports are written to `backend/reports_output/` (gitignored) and served with an inline content disposition so opening one displays it rather than downloading.

Deleting a scan (`DELETE /api/scans/{id}`, or the bulk `DELETE /api/scans`) must remove its report files from disk explicitly — SQLAlchemy's `cascade="all, delete-orphan"` on `Scan.reports`/`Scan.findings` only cleans up DB rows, not the physical files (see `_delete_scan_and_files` in `scans.py`). Both delete endpoints refuse (409) to delete a scan whose status is `pending`/`spidering`/`active_scanning`, since the orchestrator's background task still holds a live reference to it for the scan's duration; the bulk endpoint instead skips such scans and reports how many it deleted vs. skipped.

### Authorization gate

Every scan requires confirmed authorization, enforced **both** client-side (`AuthorizationGate.tsx` disables submit) and server-side (`POST /api/scans` returns 400), and stored on the scan row as an audit trail. This is a core premise of the project — do not weaken either side, and keep the server check even if UI changes.

### Persistence

SQLAlchemy 2.0 + SQLite, schema created by `Base.metadata.create_all` in the FastAPI lifespan handler. There are intentionally no Alembic migrations; model changes against an existing `sentinelscan.db` require deleting the file or hand-migrating.

### Frontend data flow

Plain `fetch` in `src/api/client.ts` plus small polling hooks (`useScanStatus` polls every 2s until a terminal status, `useFindings` loads only once a scan completes). No state library. `src/api/types.ts` mirrors the backend Pydantic schemas by hand — changing a response shape means updating both.
