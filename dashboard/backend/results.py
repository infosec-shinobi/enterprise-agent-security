"""Read-only, projected Lab 01 evidence; never return raw diagnostics."""
import hashlib
import json
import re
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from tools import evidence
from tools.validate_manifest import ROOT, load_manifest
from dashboard.backend.labs import Control

MAX_BYTES = 1000000
MANIFEST = ROOT / "labs/01-control-plane/manifest.yaml"
SAFE_REASONS = {
    "All assertions passed", "Security assertion mismatch", "Scenario execution error",
    "Execution incomplete", "Cleanup failed", "Interrupted",
    "Manifest, HTTP or Compose operation failed", "Service readiness timed out",
    "Fresh registry required", "Registry state verification failed",
    "Unexpected Lab 01 scenario contract", "Registry transition failed: draft",
    "Registry transition failed: active", "Registry transition failed: suspended",
    "Host port occupied: 8000", "Host port occupied: 8001", "Host port occupied: 8081",
    "Expected status received", "Unexpected HTTP status", "Authentication rejected",
    "Service or dependency failure", "HTTP timeout", "HTTP transport failure",
    "Unknown action", "Authentication required", "Not reached",
    "Scenario preparation or execution interrupted",
}

def safe_reason(value):
    return value if isinstance(value, str) and value in SAFE_REASONS else "Diagnostic withheld; inspect local evidence"

class Assertion(BaseModel):
    scenario: str
    controls: list[str]
    outcome: Literal["pass","fail","error","not_run"]
    expected: int
    actual: int | None
    started_at: str | None
    finished_at: str | None
    reason: str

class ResultView(BaseModel):
    schema_version: Literal[1] = 1
    run_id: str
    lab_id: Literal["lab-01"]
    outcome: Literal["pass","fail","error"]
    exit_code: int
    cleanup: Literal["success","error","not_required"]
    reason: str
    started_at: str
    finished_at: str
    duration_ms: int
    manifest_matches: bool
    scenarios: list[Assertion]
    controls: list[Control]
    control_effectiveness: Literal["not_assessed"] = "not_assessed"

def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()

def load_report(directory, run_id):
    if not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise FileNotFoundError("Unknown run")
    directory = Path(directory)
    parent = directory / "evidence"
    path = parent / (run_id + ".json")
    if linked(directory) or linked(parent) or linked(path):
        raise ValueError("Linked evidence rejected")
    if not path.is_file():
        raise FileNotFoundError("Unknown run")
    if path.resolve().parent != parent.resolve():
        raise ValueError("Unsafe evidence path")
    with path.open("rb") as f:
        raw = f.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("Oversized evidence")
    report = json.loads(raw)
    evidence.validate(report)
    if (report["run_id"],report["lab_id"],report["project"]) != (run_id,"lab-01","eas-a04-"+run_id):
        raise ValueError("Evidence identity mismatch")
    return report

def project_report(report):
    manifest = load_manifest(MANIFEST)
    contract = {s["id"]:s for s in manifest["scenarios"]}
    catalog = json.loads((ROOT/"docs/controls/controls.json").read_text(encoding="utf-8"))["controls"]
    controls = {c["id"]:Control(**c) for c in catalog}
    if len(controls)!=len(catalog):
        raise ValueError("Duplicate controls")
    matches = report["manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    rows = report["scenarios"]
    ids = [s["scenario"] for s in rows]
    if len(ids)!=len(set(ids)) or any(i not in contract for i in ids):
        raise ValueError("Unknown or duplicate scenarios")
    if matches and ids != list(contract):
        raise ValueError("Incomplete scenario contract")
    for s in rows:
        if any(c not in controls for c in s["controls"]):
            raise ValueError("Unknown controls")
        if matches and (s["controls"]!=contract[s["scenario"]]["controls"] or s["expected"]!=contract[s["scenario"]]["expected"]["http_status"]):
            raise ValueError("Scenario mapping mismatch")
    # Current catalog labels are contextual, not a historical catalog snapshot.
    return ResultView(**{k:report[k] for k in ("run_id","lab_id","outcome","exit_code","cleanup","started_at","finished_at","duration_ms")},
        reason=safe_reason(report["reason"]), manifest_matches=matches,
        scenarios=[Assertion(**{**s,"reason":safe_reason(s["reason"])}) for s in rows],
        controls=[controls[c] for c in sorted({c for s in rows for c in s["controls"]})])
