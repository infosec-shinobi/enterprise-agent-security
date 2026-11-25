# Playground — B03

Local development shell with B02 read-only manifest discovery; B03 host-side service probes; no lab execution, framework mappings or evidence ingestion yet. React/TypeScript/Vite on 127.0.0.1:5173 proxies /api to FastAPI on 127.0.0.1:8090. No Docker socket, CORS wildcard, arbitrary command endpoint or external listener. TrustedHost middleware is defense in depth, not authentication. Do not expose either development server to a network. Existing lab ports 8000/8001/8081 are unchanged.

## Architecture

See [ADR-001 — Playground application technology stack](../docs/adr/ADR-001-playground-application-stack.md) for the decision, alternatives and tradeoffs.

Frontend navigation and typed API client are independent of lab internals. Versioned /api/v1 routes expose health and capabilities. The B02 backend discovers manifests via existing validators. B03 probes allowlisted services. Future modules will invoke trusted host runner with a single-run lock (B04), stream events (B05), and read validated evidence (B06/F01). B07 handles packaging; no new Compose services in B01. Canonical control IDs remain in docs/controls/controls.json; G01 defines versioned external mapping packs, G04 projects evidence, G05 adds framework selection. No framework compliance inference. Proposed modules are not implemented yet.

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

Expect 24 tests (optional symlink skip). Start dashboard using commands above, build frontend and visit Services. With no lab running, four host endpoints should be unavailable and three internal services unknown, assuming ports are unoccupied. Start Lab 01 using docker compose up -d --build; wait for startup. Refresh Services: registry, gateway and Keycloak available; OPA and SPIRE unknown. OpenBao depends on whether optional overlay is running. Stop only gateway using docker compose stop gateway, refresh, then restore using docker compose start gateway. Stop OPA briefly only in a dedicated idle lab, refresh: gateway endpoint may still be available and OPA unknown. Restore using docker compose start opa. Do not infer enforcement from this view. Stop dashboard API, verify error, restart and refresh. Restore original lab state (docker compose stop only if you started the lab for this test; no volume deletion). Run original tools regression with integration opt-in unset. B03 validation pending.
