# Lab manifest v1

A manifest is declarative metadata, not executable code. Discovery should only scan labs/*/manifest.yaml; examples are not runnable. The runner must independently allowlist action IDs and service targets; schema validation is not authorization. Scenarios are ordered; setup/cleanup and secret handling belong to trusted runner code. HTTP status assertions are the only v1 assertion type. Control references describe intended evidence, not automatic proof of effectiveness.

## Validation

Requires Python 3.10+ and the pinned dependencies. From repository root:

### Bash (Linux/macOS)
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/manifest-requirements.txt
.venv/bin/python tools/validate_manifest.py examples/lab-manifest.yaml
.venv/bin/python tools/validate_manifest.py examples/invalid-lab-manifest.yaml
echo $?
```

### Windows PowerShell 5.1/7+
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools/manifest-requirements.txt
.\.venv\Scripts\python.exe tools/validate_manifest.py examples/lab-manifest.yaml
.\.venv\Scripts\python.exe tools/validate_manifest.py examples/invalid-lab-manifest.yaml
$LASTEXITCODE
```

Expected: valid example prints VALID and exits 0; invalid example prints INVALID and exits 1 because the status is a string. No Docker services are needed. If py is unavailable, use python instead. Validation also rejects unknown control IDs, duplicate scenario IDs, duplicate YAML keys, aliases and unknown fields. It does not verify that action IDs have implementations or that services are running.

## Cleanup

The virtual environment can be reused for A02. To remove it:

Bash: `rm -rf .venv` (from repository root).

PowerShell: `Remove-Item -Recurse -Force .venv` (from repository root).

## Status

A01 complete: user confirmed both fixtures behaved as expected on Windows PowerShell (valid accepted; invalid HTTP status string rejected with exit code 1). Linux/macOS and additional negative cases remain untested. A02 will add the actual Lab 01 manifest.
