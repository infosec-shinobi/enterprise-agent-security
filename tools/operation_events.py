"""Bounded, fixed-vocabulary runner observations. Never emit raw logs."""
import json
from pathlib import Path

MAX_BYTES = 32768
MAX_EVENTS = 128
PHASES = {"manifest_validated", "provisioning", "services_ready", "authenticated",
          "cleanup_started", "cleanup_succeeded", "cleanup_failed", "evidence_saved",
          "runner_error"}
SCENARIOS = {"unregistered-read", "draft-read", "active-read", "active-delete", "suspended-read"}

def normalize(row):
    if not isinstance(row, dict):
        return None
    kind = row.get("kind")
    if isinstance(kind, str) and kind in PHASES and set(row) == {"kind"}:
        return {"kind": kind}
    if kind == "assertion" and set(row) == {"kind","scenario","outcome","expected","actual"}:
        if (isinstance(row["scenario"], str) and row["scenario"] in SCENARIOS
            and row["outcome"] in ("pass","fail","error")
            and type(row["expected"]) is int and 100 <= row["expected"] <= 599
            and (row["actual"] is None or type(row["actual"]) is int and 100 <= row["actual"] <= 599)):
            return dict(row)
    return None

class Emitter:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.count = 0
        self.size = 0

    def emit(self, kind, **fields):
        if self.path is None or self.count >= MAX_EVENTS:
            return
        row = normalize(dict(kind=kind, **fields))
        if row is None:
            return
        data = (json.dumps(row, separators=(",",":"))+"\n").encode("ascii")
        if self.size + len(data) > MAX_BYTES:
            return
        try:
            with self.path.open("ab") as f:
                f.write(data)
            self.count += 1
            self.size += len(data)
        except OSError:
            # Observability must not alter assertions or cleanup.
            self.path = None
