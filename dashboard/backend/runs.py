"""Trusted local runner adapter; no arbitrary command or output API."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from fastapi.responses import StreamingResponse
from dashboard.backend.events import Journal
import uuid
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from jsonschema import ValidationError
from tools.validate_manifest import ROOT
from tools import evidence

ADAPTERS = {"lab-01": ROOT / "tools/run_lab01.py"}
TIMEOUT = 1000
ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173",
           "http://127.0.0.1:8090", "http://localhost:8090"}
router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

def now():
    return datetime.now(timezone.utc).isoformat()

class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lab_id: str

class Run(BaseModel):
    run_id: str
    lab_id: str
    project: str
    status: Literal["running", "pass", "fail", "error"]
    started_at: str
    finished_at: str | None = None
    exit_code: int | None = None
    evidence_path: str | None = None
    reason: str
    recovery_required: bool = False

class Snapshot(BaseModel):
    supported_labs: list[str]
    blocked: bool
    latest: Run | None

class Busy(Exception):
    pass

def local_environment():
    # Host administrator owns Docker configuration. Pin the inspected local context.
    env = os.environ.copy()
    if env.get("DOCKER_HOST"):
        raise ValueError("Explicit Docker host is not supported")
    context = subprocess.run(["docker","context","show"], cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10, check=True).stdout.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", context):
        raise ValueError("Invalid Docker context")
    endpoint = subprocess.run(["docker","context","inspect",context,"--format","{{.Endpoints.docker.Host}}"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, timeout=10, check=True).stdout.strip()
    if not endpoint.startswith(("unix:///", "npipe:////./pipe/")):
        raise ValueError("Only local Docker sockets are supported")
    env["DOCKER_CONTEXT"] = context
    return env

class Manager:
    def __init__(self, directory=ROOT / "data", launch=None):
        self.directory = Path(directory)
        self.marker = self.directory / "dashboard-run.lock"
        self.guard = threading.Lock()
        self.latest = None
        self.journal = None
        self.stream_slots = threading.BoundedSemaphore(8)
        self.launch = launch or self.execute

    def snapshot(self):
        with self.guard:
            return Snapshot(supported_labs=list(ADAPTERS), blocked=self.marker.exists(),
                            latest=self.latest)

    def start(self, lab_id):
        if lab_id not in ADAPTERS:
            raise KeyError(lab_id)
        with self.guard:
            self.directory.mkdir(parents=True, exist_ok=True)
            run_id = uuid.uuid4().hex
            run = Run(run_id=run_id, lab_id=lab_id, project="eas-a04-"+run_id,
                      status="running", started_at=now(), reason="Runner accepted")
            try:
                with self.marker.open("x", encoding="utf-8") as f:
                    json.dump({"run_id":run_id,"project":run.project},f)
                    f.flush()
                    os.fsync(f.fileno())
            except FileExistsError:
                raise Busy from None
            self.latest = run
            self.journal = Journal(run_id)
            self.journal.append('accepted')
            try:
                threading.Thread(target=self.worker, args=(run,), daemon=False).start()
            except RuntimeError:
                self.latest = run.model_copy(update={"status":"error","finished_at":now(),
                    "reason":"Worker could not start","recovery_required":True})
                self.journal.finish("error", True)
            return run

    def execute(self, run):
        env = local_environment()
        path = self.directory / ("events-"+run.run_id+".jsonl")
        with path.open("xb"):
            pass
        try:
            with subprocess.Popen([sys.executable, "-E", "-s", str(ADAPTERS[run.lab_id]), "--run-id", run.run_id, "--events"],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL) as child:
                deadline = time.monotonic()+TIMEOUT
                try:
                    while True:
                        self.journal.ingest(path)
                        code = child.poll()
                        if code is not None:
                            self.journal.ingest(path)
                            return code
                        if time.monotonic() >= deadline:
                            raise subprocess.TimeoutExpired("trusted runner", TIMEOUT)
                        time.sleep(.25)
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.wait()
        finally:
            try:
                path.unlink()
            except OSError:
                pass

    def worker(self, run):
        code = None
        updates = {"status":"error","reason":"Execution or evidence verification failed",
                   "recovery_required":True}
        try:
            code = self.launch(run)
            path = self.directory / "evidence" / (run.run_id+".json")
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 1000000:
                raise ValueError("Evidence missing or unsafe")
            report = json.loads(path.read_text(encoding="utf-8"))
            evidence.validate(report)
            if (report["run_id"],report["lab_id"],report["project"],report["exit_code"]) != (
                run.run_id,run.lab_id,run.project,code):
                raise ValueError("Evidence mismatch")
            updates["evidence_path"] = "data/evidence/"+run.run_id+".json"
            if report["cleanup"] not in ("success","not_required"):
                raise ValueError("Cleanup not confirmed")
            updates.update(status=report["outcome"], reason="Validated runner evidence",
                           recovery_required=False)
        except subprocess.TimeoutExpired:
            updates["reason"] = "Runner deadline exceeded; inspect disposable project"
        except (OSError, ValueError, ValidationError, subprocess.SubprocessError, KeyError, TypeError, RecursionError):
            pass
        finally:
            with self.guard:
                if not updates["recovery_required"]:
                    try:
                        self.marker.unlink()
                    except OSError:
                        updates.update(status="error",reason="Run lock could not be released",recovery_required=True)
                self.latest = run.model_copy(update={**updates,"exit_code":code,"finished_at":now()})
                self.journal.finish(self.latest.status, self.latest.recovery_required)

manager = Manager()

@router.get("", response_model=Snapshot)
def list_runs(response: Response):
    response.headers["Cache-Control"]="no-store"
    return manager.snapshot()

@router.get("/{run_id}", response_model=Run)
def get_run(run_id: str, response: Response):
    response.headers["Cache-Control"]="no-store"
    run = manager.snapshot().latest
    if run is None or run.run_id != run_id:
        raise HTTPException(404,"Run not found")
    return run

@router.post("", response_model=Run, status_code=202)
def start_run(body: Start, request: Request, response: Response):
    if (request.headers.get("origin") not in ORIGINS or
        request.headers.get("x-eas-action") != "start-run" or
        request.headers.get("content-type","").split(";")[0].strip().lower() != "application/json"):
        raise HTTPException(403,"Execution request rejected")
    response.headers["Cache-Control"]="no-store"
    try:
        return manager.start(body.lab_id)
    except KeyError:
        raise HTTPException(404,"No trusted runner for lab") from None
    except Busy:
        raise HTTPException(409,"Run active or recovery required") from None
    except OSError:
        raise HTTPException(503,"Execution state unavailable") from None


@router.get("/{run_id}/events")
async def run_events(run_id: str, request: Request):
    with manager.guard:
        journal = manager.journal
        slots = manager.stream_slots
        if journal is None or journal.operation_id != run_id:
            raise HTTPException(404, "Run not found")
    origin = request.headers.get("origin")
    if origin is not None and origin not in ORIGINS:
        raise HTTPException(403, "Origin rejected")
    raw = request.headers.get("last-event-id", "0")
    if not re.fullmatch(r"[0-9]{1,4}", raw):
        raise HTTPException(400, "Invalid event cursor")
    cursor = int(raw)
    if cursor > journal.read(0)[2]:
        raise HTTPException(400, "Invalid event cursor")
    if not slots.acquire(blocking=False):
        raise HTTPException(429, "Too many event streams")
    async def body():
        try:
            async for frame in journal.stream(cursor, request):
                yield frame
        finally:
            slots.release()
    return StreamingResponse(body(), media_type="text/event-stream",
        headers={"Cache-Control":"no-store", "X-Accel-Buffering":"no"})
