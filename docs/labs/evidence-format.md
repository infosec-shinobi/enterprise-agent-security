# A05 — Run evidence v1

JSON Schema Draft 2020-12; HTTP assertions only. One report per run under data/evidence/<run-id>.json (already ignored by Git). UTC timestamps, monotonic duration, SHA-256 of manifest, scenario control IDs, expected/actual status, outcome, reason, cleanup and exit code. The manifest hash is not full build provenance. No raw HTTP headers, bodies, tokens or exception dumps. Reports are local and editable, not signed or tamper-proof. Atomic replacement prevents partially written final files during normal persistence; forced termination before finalization can leave no report. Invalid manifests can produce a run error with no scenarios. No retention policy yet.

Exit codes for runner and report CLI: 0 pass, 1 assertion failure, 2 execution or cleanup error (or evidence read/write failure). Report CLI validates before displaying, does not run a lab. Not-run scenarios have null actual and timestamps. A blocked port yields error, cleanup not_required, all scenarios not_run.

## PowerShell
```powershell
git pull origin main
.\.venv\Scripts\python.exe -m unittest discover -s tools -p "test_*.py" -v
docker compose stop
.\.venv\Scripts\python.exe tools/run_lab01.py
$LASTEXITCODE
$report = Get-ChildItem data/evidence/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\.venv\Scripts\python.exe tools/report_evidence.py $report.FullName
$LASTEXITCODE
docker compose start
.\.venv\Scripts\python.exe tools/run_lab01.py
$LASTEXITCODE
$report = Get-ChildItem data/evidence/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\.venv\Scripts\python.exe tools/report_evidence.py $report.FullName --json
$LASTEXITCODE
```

## Bash
```bash
git pull origin main
.venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v
docker compose stop
.venv/bin/python tools/run_lab01.py
echo $?
report=$(ls -t data/evidence/*.json | head -n 1)
.venv/bin/python tools/report_evidence.py "$report"
echo $?
docker compose start
.venv/bin/python tools/run_lab01.py
echo $?
report=$(ls -t data/evidence/*.json | head -n 1)
.venv/bin/python tools/report_evidence.py "$report" --json
echo $?
```

Use an existing manual Compose project for blocked-port test; confirm its ports are bound. Expected seven unit tests, successful report (five passes, cleanup success), blocked report (five not_run, cleanup not_required, exit 2). Use exact printed evidence path if running other tests concurrently. Validation complete (user-reported Windows PowerShell): all seven unit tests and all 12 A05 acceptance checks passed. Successful run returned exit 0 and persisted metadata, expected/actual statuses, control mappings and successful cleanup; report CLI displayed results. Occupied-port run returned exit 2 and persisted five not_run scenarios. Separate evidence files retained and excluded from Git. Live assertion mismatch, injected dependency failure, cleanup failure, persistence failure, forced termination and Linux/macOS remain unverified.
