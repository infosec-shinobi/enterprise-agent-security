# Playground — B05

Local development shell with B02 read-only manifest discovery; B03 host-side service probes; B04 allowlisted Lab 01 execution; no framework mappings or historical evidence ingestion yet. React/TypeScript/Vite on 127.0.0.1:5173 proxies /api to FastAPI on 127.0.0.1:8090. No Docker socket, CORS wildcard, arbitrary command endpoint or external listener. TrustedHost middleware is defense in depth, not authentication. Do not expose either development server to a network. Existing lab ports 8000/8001/8081 are unchanged.

## Architecture

See [ADR-001 — Playground application technology stack](../docs/adr/ADR-001-playground-application-stack.md) for the decision, alternatives and tradeoffs.

Frontend navigation and typed API client are independent of lab internals. Versioned /api/v1 routes expose health and capabilities. The B02 backend discovers manifests via existing validators. B03 probes allowlisted services. B04 invokes the trusted host runner with a persistent dashboard lock. B05 streams structured observations; B06/F01 will display detailed evidence. B07 handles packaging; no new Compose services in B01. Canonical control IDs remain in docs/controls/controls.json; G01 defines versioned external mapping packs, G04 projects evidence, G05 adds framework selection. No framework compliance inference. Proposed modules are not implemented yet.

## Prerequisites

Python 3.10+ and Node.js 22 LTS or newer supported LTS, npm, existing repository virtual environment. Run commands from repository root unless noted. Direct dependencies pinned; npm generates a lockfile on first install, which should be reviewed and committed for reproducible npm ci later. Transitive Python dependencies not locked yet. No security audit or runtime verification performed by author.

## PowerShell — terminal 1
```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r dashboard/backend/requirements.txt
.\.venv\Scripts\python.exe -m unittest dashboard.backend.test_api -v
.\.venv\Scripts\python.exe -m uvicorn dashboard.backend.main:app --host 127.0.0.1 --port 8090
```

## Bash — terminal 1
```bash
git pull origin main
.venv/bin/python -m pip install -r dashboard/backend/requirements.txt
.venv/bin/python -m unittest dashboard.backend.test_api -v
.venv/bin/python -m uvicorn dashboard.backend.main:app --host 127.0.0.1 --port 8090
```

## Terminal 2 — both shells (repository root)
```sh
node --version
npm --version
cd dashboard/frontend
npm install
npm run build
npm run dev
```

Open http://127.0.0.1:5173. Direct API docs http://127.0.0.1:8090/docs. Four API tests should pass, build should succeed, UI should report Connected. Navigate all pages; Overview/connectivity and Labs discovery are implemented. Toggle theme and reload to verify persistence. Stop backend with Ctrl+C and click Refresh; expect Unavailable. Restart backend and refresh; expect Connected. Stop both servers with Ctrl+C. Existing Docker services need not be stopped.

## Regression

From root, with integration opt-in unset, run existing tools unittest discovery (PowerShell: .\.venv\Scripts\python.exe -m unittest discover -s tools -p "test_*.py" -v; Bash: .venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v). Expect 22 passes and one skip. B01 validated by user on Windows: all 14 acceptance checks passed, including four API tests, frontend build, navigation, theme persistence, API failure/recovery and existing regression suite. Linux/macOS, dependency lockfile review and security audit remain outstanding.

## B02 — Lab discovery

See [ADR-002](../docs/adr/ADR-002-manifest-driven-lab-discovery.md). GET /api/v1/labs returns labs and issues; GET /api/v1/labs/lab-01 returns details. Unknown IDs return 404, unavailable catalog returns 503. Missing manifests are not discovered. Invalid entries are excluded with fixed diagnostic reasons. No execution or framework compliance claims.

Stop the prior development servers, pull main, reinstall backend requirements using the commands above and run:

PowerShell:
```powershell
.\.venv\Scripts\python.exe -m unittest dashboard.backend.test_api dashboard.backend.test_labs -v
```

Bash:
```bash
.venv/bin/python -m unittest dashboard.backend.test_api dashboard.backend.test_labs -v
```

Expected 12 tests, all pass or one symlink test skipped if OS permissions prohibit creating links. Restart API and rerun npm run build / npm run dev. Open Labs, verify Lab 01 shows five scenarios, six mapped controls and four required services. Expand both detail panels. Stop backend and refresh labs to verify error state; restart and retry. Re-run existing 23-test discovery with integration disabled. B02 validated by user on Windows: backend and original regression suites, API endpoints, frontend build, scenario/control details, themes, dynamic discovery and removal, duplicate-ID exclusion and diagnostics, and API failure/recovery all passed. Exact symlink skip count not reported. No new frontend dependencies.

### Optional manual discovery fixture (PowerShell)

From the repository root, use a new temporary directory (do not reuse an existing directory):

```powershell
New-Item -ItemType Directory labs/b02-discovery-test -ErrorAction Stop
Copy-Item labs/01-control-plane/README.md labs/b02-discovery-test/README.md
(Get-Content labs/01-control-plane/manifest.yaml -Raw) -replace '(?m)^id: lab-01\r?$', 'id: lab-99' | Set-Content labs/b02-discovery-test/manifest.yaml -Encoding UTF8
Select-String -Path labs/b02-discovery-test/manifest.yaml -Pattern '^id:'
```

Verify lab-99, refresh Labs and expect both cards. The optional carriage return handles Windows CRLF. Duplicate IDs instead exclude both entries; this behavior was manually validated. Remove the fixture after testing:

```powershell
Remove-Item labs/b02-discovery-test/README.md
Remove-Item labs/b02-discovery-test/manifest.yaml
Remove-Item labs/b02-discovery-test
```

Refresh and verify only Lab 01 remains.

## B03 — Service observations

See [ADR-003](../docs/adr/ADR-003-bounded-service-observations.md). GET /api/v1/services and GET /api/v1/services/{service_id} return point-in-time observations. No Docker socket or Compose changes. Unknown or failed observations do not establish container state. Control effectiveness always not_assessed.

From repository root with prior servers stopped and changes pulled:

PowerShell:
```powershell
.\.venv\Scripts\python.exe -m unittest dashboard.backend.test_api dashboard.backend.test_labs dashboard.backend.test_services -v
```

Bash:
```bash
.venv/bin/python -m unittest dashboard.backend.test_api dashboard.backend.test_labs dashboard.backend.test_services -v
```

Expect 24 tests (optional symlink skip). Start dashboard using commands above, build frontend and visit Services. With no lab running, four host endpoints should be unavailable and three internal services unknown, assuming ports are unoccupied. Start Lab 01 using docker compose up -d --build; wait for startup. Refresh Services: registry, gateway and Keycloak available; OPA and SPIRE unknown. OpenBao depends on whether optional overlay is running. Stop only gateway using docker compose stop gateway, refresh, then restore using docker compose start gateway. Stop OPA briefly only in a dedicated idle lab, refresh: gateway endpoint may still be available and OPA unknown. Restore using docker compose start opa. Do not infer enforcement from this view. Stop dashboard API, verify error, restart and refresh. Restore original lab state (docker compose stop only if you started the lab for this test; no volume deletion). Run original tools regression with integration opt-in unset. B03 validated on Windows by user: all 18 acceptance checks and optional live OpenBao test passed. Exact symlink skip count not reported. Linux/macOS remain unverified.

### Planned monitoring expansion

See roadmap H01–H05 for internal OPA/SPIRE observations, per-service coverage, and optional LiteLLM/Bifrost model gateway profiles. B03 unknown states remain accurate until those probes are implemented. No provider or collector implementation is included in B03.

## B04 — Trusted execution

See [ADR-004](../docs/adr/ADR-004-trusted-runner-execution.md). Start the API as a single worker without reload, using the existing virtual environment. Run the application tests:

PowerShell:
```powershell
.\.venv\Scripts\python.exe -m unittest dashboard.backend.test_api dashboard.backend.test_labs dashboard.backend.test_services dashboard.backend.test_runs -v
```
Bash:
```bash
.venv/bin/python -m unittest dashboard.backend.test_api dashboard.backend.test_labs dashboard.backend.test_services dashboard.backend.test_runs -v
```

Expect 33 tests, optional symlink skip. Build and start frontend. Ensure local Docker context and ports 8000/8001/8081 free, no concurrent CLI or Compose operations. Stop existing Lab 01 services only if safe; do not delete volumes. Open Runs, click Run Lab 01 and confirm. Observe running then pass, exit 0, evidence path. Refresh or navigate away and back during execution; run continues. Verify duplicate POST returns 409 while active. Verify evidence using existing report CLI and scoped project resource checks. Repeat with a new run ID. Start existing Lab 01 manually, then submit a run: expect error exit 2, evidence with not_required cleanup and occupied-port reason; original environment preserved. Restore original state. Run original tools regression. B04 validated by user on 2026-11-25. Individual acceptance results, exact test/skip counts and platform were not restated; author did not independently execute validation. B05 is next.

API POST /api/v1/runs accepts only JSON {"lab_id":"lab-01"} with Origin http://127.0.0.1:5173 and X-EAS-Action: start-run (other exact local development origins in ADR implementation). GET /api/v1/runs returns latest and lock state; GET /api/v1/runs/{id} returns latest matching ID. No raw logs or cancellation; B05 adds structured events. Browser disconnect does not cancel. Latest status is not durable; evidence is.

### Recovery (only if lock persists)

Do not delete data/dashboard-run.lock while any runner or Compose operation is active. Stop the dashboard after verifying the worker is no longer active, inspect the marker for the exact project and confirm local Docker context. Check runner/Compose processes and Docker resources. If uncertain, leave the lock in place. Only after confirming no in-flight operations remain, use docker compose -f compose.yaml -p <recorded-project> down -v for that exact disposable eas-a04-UUID project (never default project). Verify no matching containers, volumes or networks remain. Then remove only data/dashboard-run.lock and restart dashboard. Do not automatically retry or delete evidence. Forced termination may leave descendants; this is manual recovery, not a cleanup guarantee.

## Planned Free Lab mode

Phase I in the [roadmap](../ROADMAP.md) adds persistent, independently configurable experimentation alongside manual, autopilot and sandbox modes. It depends on reviewed provisioning (C07), environment isolation and monitoring contracts (I01/H01), and MVP packaging (B07). Native service interfaces and a dedicated experiment container support custom scripts without an arbitrary host command API. Free Lab is not implemented yet.

## B05 — Structured operation events

See [ADR-005](../docs/adr/ADR-005-structured-operation-events.md). Run the B04 application test command with dashboard.backend.test_events appended (40 tests expected, optional symlink skip). Run original tools regression and npm run build. Start single-worker API and frontend as above. With lab ports free, start Lab 01 from Runs. Observe accepted, manifest validation, provisioning, readiness/authentication, five assertion events, cleanup, evidence saved and terminal outcome. Verify sequence IDs increase, no credentials or raw logs, and final status matches validated evidence. Navigate away and back or reload during execution: replay from beginning, no duplicate sequence IDs, no new execution. For a completed run, use curl.exe (PowerShell) or curl (Bash) -N -H "Last-Event-ID: 3" http://127.0.0.1:8090/api/v1/runs/<run-id>/events; expect only IDs greater than 3 and terminal close. Invalid cursor 400, unknown run 404. Repeat occupied-port test: no invented readiness or assertions, terminal error, original infrastructure preserved. Verify lock release and scoped cleanup on successful run. User confirmed 17 of 18 acceptance checks passed on 2026-11-25: dashboard and tools regression, frontend build, live events, assertion results, ordered SSE replay and reconnect, invalid cursor rejection, browser independence, evidence agreement, lock release, scoped cleanup and occupied-port protection. Original tools suite reported 22 tests and one skip; discrepancy from expected 23 remains unreconciled. Light/dark timeline verification outstanding, carried into B06. No independent execution by author.

Event journal is latest-run only and memory resident; restart loses replay, not evidence. Spool is bounded to 32 KiB / 128 runner observations and removed after supervision; abnormal termination can leave ignored files. Eight simultaneous SSE streams maximum. Heartbeats approximately every 10 seconds. REST polling remains authoritative. Sandbox and Free Lab adapters are planned, not implemented. No new dependencies.
