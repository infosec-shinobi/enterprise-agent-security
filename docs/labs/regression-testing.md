# A06 — Regression testing

Use existing runner dependencies and Python 3.10+. Offline discovery runs 22 tests plus one skipped integration test by default. HTTPX MockTransport and unittest.mock simulate responses and infrastructure failures without live network or Docker. Mocked outcomes are not evidence of actual enforcement.

Coverage: malformed manifests, duplicate IDs/keys, unknown controls, YAML aliases and size limits; redirect refusal, missing/malformed tokens, existing timeout/status tests; ordered lifecycle and same token, failed transition, wrong state, dependency error, unauthorized delete, expired token; occupied ports, startup/cleanup/persistence errors; evidence consistency, distinct files, atomic write failure and invalid report CLI.

Integration explicitly opts in and runs two real isolated Lab 01 executions, validates both persisted reports and checks project-labeled containers, networks and volumes are removed. It does not inject faults into live services. Run only against local Docker Desktop/Engine, with ports 8000, 8001, 8081 free. Stop the manual project without deleting its volumes. No parallel runs. If forcibly interrupted, inspect the printed project or Docker project list and recover only the disposable project as described in lifecycle-runner.md.

## PowerShell
```powershell
git pull origin main
Remove-Item Env:EAS_RUN_INTEGRATION -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m unittest discover -s tools -p "test_*.py" -v
$LASTEXITCODE
docker context show
docker compose stop
$env:EAS_RUN_INTEGRATION = "1"
try {
    .\.venv\Scripts\python.exe -m unittest discover -s tools -p test_compose_integration.py -v
    $LASTEXITCODE
} finally {
    Remove-Item Env:EAS_RUN_INTEGRATION -ErrorAction SilentlyContinue
}
docker compose ls -a
```

## Bash
```bash
git pull origin main
unset EAS_RUN_INTEGRATION
.venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v
echo $?
docker context show
docker compose stop
EAS_RUN_INTEGRATION=1 .venv/bin/python -m unittest discover -s tools -p test_compose_integration.py -v
echo $?
docker compose ls -a
```

Expected offline: Ran 23 tests, OK (skipped=1), exit 0. Expected integration: Ran 1 test, OK, exit 0 (two real runs). Restart the original manual project with docker compose start if desired. Evidence remains under data/evidence. Record platform and actual results separately. No CI or coverage percentage yet; gateway internals, live fault injection, concurrency and forced termination recovery remain outside this suite. Validation complete: user confirmed all ten acceptance checks on Windows, including 22 offline passes, one intentional skip, opt-in integration pass (two real runs), distinct evidence and resource cleanup. Other platforms and live failure injection remain unverified.
