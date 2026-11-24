# A03 HTTP runner

Host-local Python runner using httpx, fixed action IDs and fixed localhost endpoints. No arbitrary URLs, redirects, environment proxies, or lifecycle mutations. Tokens stay in memory and results omit headers, bodies and exception details. Do not enable HTTP wire debugging. Timeout is five seconds per HTTP operation phase, not a total run deadline. The smoke CLI acquires a new token per invocation; it cannot prove same-token suspension. A04 will verify lifecycle preconditions and reuse a token within an isolated run. A05 will formalize evidence.

## Tests from repository root

Bash:
```bash
.venv/bin/python -m pip install -r tools/runner-requirements.txt
.venv/bin/python -m unittest discover -s tools -p test_http_runner.py -v
.venv/bin/python tools/validate_manifest.py labs/01-control-plane/manifest.yaml
docker compose up --build -d
docker compose ps
.venv/bin/python tools/runner_smoke.py unregistered-read
echo $?
```

PowerShell:
```powershell
.\.venv\Scripts\python.exe -m pip install -r tools/runner-requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tools -p test_http_runner.py -v
.\.venv\Scripts\python.exe tools/validate_manifest.py labs/01-control-plane/manifest.yaml
docker compose up --build -d
docker compose ps
.\.venv\Scripts\python.exe tools/runner_smoke.py unregistered-read
$LASTEXITCODE
```

Wait for Keycloak readiness before the smoke test. It assumes an unregistered agent in the existing registry. If state persists from Lab 01, do not infer state from 403: inspect registry GET /internal/agents/agent-demo (localhost:8000); 404 is required. Reset only if willing to delete local lab volumes, using docker compose down -v and restarting. Expected four unit tests OK, manifest VALID, smoke outcome pass expected/actual 403 exit 0. Exit 1 means assertion mismatch, 2 means execution error. A 401 or 503 does not pass an expected 403. No live execution has yet been verified for A03.
