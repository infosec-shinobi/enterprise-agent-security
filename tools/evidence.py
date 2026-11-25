"""Versioned HTTP lab evidence; no request or response payloads."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from jsonschema import Draft202012Validator, FormatChecker
if __package__:
    from .validate_manifest import ROOT
else:
    from validate_manifest import ROOT

SCHEMA = ROOT / "schemas/run-evidence.schema.json"
OUTPUT = ROOT / "data" / "evidence"

def now():
    return datetime.now(timezone.utc).isoformat()

def new_run(run_id, project):
    return dict(schema_version=1, run_id=run_id, lab_id="lab-01", project=project,
                started_at=now(), finished_at=None, duration_ms=0,
                manifest_sha256=None, outcome="error", exit_code=2,
                reason="Execution incomplete", cleanup="not_required", scenarios=[])

def initialize(run, manifest, path):
    run["lab_id"] = manifest["id"]
    run["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    run["scenarios"] = [
        dict(scenario=s["id"], controls=s["controls"], started_at=None,
             finished_at=None, outcome="not_run", expected=s["expected"]["http_status"],
             actual=None, reason="Not reached")
        for s in manifest["scenarios"]
    ]

def finish(run, code, started):
    run["finished_at"] = now()
    run["duration_ms"] = round((time.monotonic() - started) * 1000)
    run["exit_code"] = code
    run["outcome"] = {0:"pass", 1:"fail", 2:"error"}[code]

def validate(run):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(run)
    if run["outcome"] != {0:"pass",1:"fail",2:"error"}[run["exit_code"]]:
        raise ValueError("Inconsistent exit code")
    if run["exit_code"] == 0 and (not run["scenarios"] or run["cleanup"] != "success" or any(s["outcome"] != "pass" for s in run["scenarios"])):
        raise ValueError("Incomplete successful run")
    for s in run["scenarios"]:
        if s["outcome"] == "pass" and s["actual"] != s["expected"]:
            raise ValueError("Inconsistent passing assertion")
        if s["outcome"] == "not_run" and any(s[k] is not None for k in ("actual","started_at","finished_at")):
            raise ValueError("Inconsistent unexecuted assertion")

def save(run, directory=OUTPUT):
    validate(run)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (run["run_id"] + ".json")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as file:
            temporary = Path(file.name)
            json.dump(run, file, indent=2, allow_nan=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
