# Playground — B01

Local development shell; no lab execution, service probes, framework mappings or evidence ingestion yet. React/TypeScript/Vite on 127.0.0.1:5173 proxies /api to FastAPI on 127.0.0.1:8090. No Docker socket, CORS wildcard, arbitrary command endpoint or external listener. TrustedHost middleware is defense in depth, not authentication. Do not expose either development server to a network. Existing lab ports 8000/8001/8081 are unchanged.

## Architecture

Frontend navigation and typed API client are independent of lab internals. Versioned /api/v1 routes expose health and capabilities. Future backend modules will discover manifests via existing validators (B02), probe services (B03), invoke trusted host runner with a single-run lock (B04), stream events (B05), and read validated evidence (B06/F01). B07 handles packaging; no new Compose services in B01. Canonical control IDs remain in docs/controls/controls.json; G01 defines versioned external mapping packs, G04 projects evidence, G05 adds framework selection. No framework compliance inference. Proposed modules are not implemented yet.

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

Open http://127.0.0.1:5173. Direct API docs http://127.0.0.1:8090/docs. Four API tests should pass, build should succeed, UI should report Connected. Navigate all pages; only Overview/connectivity is implemented. Toggle theme and reload to verify persistence. Stop backend with Ctrl+C and click Refresh; expect Unavailable. Restart backend and refresh; expect Connected. Stop both servers with Ctrl+C. Existing Docker services need not be stopped.

## Regression

From root, with integration opt-in unset, run existing tools unittest discovery (PowerShell: .\.venv\Scripts\python.exe -m unittest discover -s tools -p "test_*.py" -v; Bash: .venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v). Expect 22 passes and one skip. B01 validated by user on Windows: all 14 acceptance checks passed, including four API tests, frontend build, navigation, theme persistence, API failure/recovery and existing regression suite. Linux/macOS, dependency lockfile review and security audit remain outstanding.
