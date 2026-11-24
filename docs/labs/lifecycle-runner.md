# A04 — Automated Lab 01 lifecycle

The host CLI creates a random eas-a04-* Compose project using the existing compose.yaml, verifies fresh registry state, obtains a token once, verifies each transition, and runs the five manifest assertions. It stops at the first failed assertion. Cleanup runs in finally and targets only that project with down -v. Docker images/build cache remain. Fixed localhost ports mean the manual project must be stopped; no simultaneous runs are supported. Do not run against a remote Docker context. No Docker socket is exposed to the application.

## PowerShell
```powershell
git pull origin main
docker compose stop
.\.venv\Scripts\python.exe -m unittest discover -s tools -p test_http_runner.py -v
.\.venv\Scripts\python.exe tools/run_lab01.py
$LASTEXITCODE
.\.venv\Scripts\python.exe tools/run_lab01.py
$LASTEXITCODE
docker compose ls -a
```

## Bash
```bash
git pull origin main
docker compose stop
.venv/bin/python -m unittest discover -s tools -p test_http_runner.py -v
.venv/bin/python tools/run_lab01.py
echo $?
.venv/bin/python tools/run_lab01.py
echo $?
docker compose ls -a
```

Use A03 dependencies and a local Docker Engine/Desktop. Expected two distinct projects, each yielding 403/403/200/403/403, cleanup complete, exit 0. No temporary project should remain. Existing manual project and volume are preserved. Restart the manual project with docker compose start if desired (both shells). To test occupied ports, start manual project and rerun CLI: expected error and exit 2, no temporary project created. This is not a concurrency lock.

If cleanup fails or the process is forcibly killed, inspect the exact printed project name and run docker compose -f compose.yaml -p <printed-project-name> down -v only for that disposable project (both shells; replace placeholder). Do not use the default project name. Compose output is suppressed to avoid dumping environment or secrets; troubleshooting currently requires inspecting Docker state or running manual commands. Readiness covers registry/gateway health and token acquisition; OPA is exercised by the first assertion. HTTP timeouts are per phase; startup/cleanup subprocesses have separate timeouts. Token expiry is an error, never refreshed mid-run. Registry 5xx is now treated as a dependency failure by gateway.

Implementation published; execution pending. No full lifecycle or repeatability test yet verified.
