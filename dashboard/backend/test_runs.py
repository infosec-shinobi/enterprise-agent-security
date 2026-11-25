import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from dashboard.backend.main import app
from dashboard.backend.runs import Manager, Busy, local_environment
from tools import evidence

HEADERS={"Origin":"http://127.0.0.1:5173","X-EAS-Action":"start-run"}

class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)

    def wait(self, manager):
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            row=manager.snapshot().latest
            if row and row.status!="running":
                return row
            time.sleep(.01)
        self.fail("Worker did not finish")

    def report(self, run, code=2, cleanup="not_required", mismatch=False):
        report=evidence.new_run(run.run_id,run.project)
        report["cleanup"]=cleanup
        evidence.finish(report,code,time.monotonic())
        if mismatch:
            report["project"]="other"
        evidence.save(report,self.directory/"evidence")
        return code

    def test_valid_evidence_unlocks(self):
        m=Manager(self.directory,self.report)
        run=m.start("lab-01")
        row=self.wait(m)
        self.assertEqual(row.status,"error")
        self.assertFalse(row.recovery_required)
        self.assertFalse(m.snapshot().blocked)
        self.assertEqual(row.evidence_path,"data/evidence/"+run.run_id+".json")

    def test_single_run_across_managers(self):
        release=threading.Event()
        def launch(run):
            release.wait(3)
            return self.report(run)
        m=Manager(self.directory,launch)
        m.start("lab-01")
        try:
            with self.assertRaises(Busy):
                m.start("lab-01")
            with self.assertRaises(Busy):
                Manager(self.directory,launch).start("lab-01")
        finally:
            release.set()
            self.wait(m)

    def test_missing_evidence_blocks(self):
        m=Manager(self.directory,lambda r:0)
        m.start("lab-01")
        self.assertTrue(self.wait(m).recovery_required)
        self.assertTrue(Manager(self.directory).snapshot().blocked)

    def test_mismatch_blocks(self):
        m=Manager(self.directory,lambda r:self.report(r,mismatch=True))
        m.start("lab-01")
        self.assertTrue(self.wait(m).recovery_required)

    def test_cleanup_error_blocks(self):
        m=Manager(self.directory,lambda r:self.report(r,cleanup="error"))
        m.start("lab-01")
        self.assertTrue(self.wait(m).recovery_required)

    def test_timeout_blocks(self):
        def launch(r):
            raise subprocess.TimeoutExpired("runner",1)
        m=Manager(self.directory,launch)
        m.start("lab-01")
        self.assertIn("deadline",self.wait(m).reason)
        self.assertTrue(m.snapshot().blocked)

    def test_api(self):
        release=threading.Event()
        def launch(r):
            release.wait(3)
            return self.report(r)
        m=Manager(self.directory,launch)
        with patch("dashboard.backend.runs.manager",m), TestClient(app) as c:
            self.assertEqual(c.post("/api/v1/runs",json={"lab_id":"lab-01"}).status_code,403)
            self.assertEqual(c.post("/api/v1/runs",json={"lab_id":"lab-01"},headers={**HEADERS,"Origin":"https://example.invalid"}).status_code,403)
            self.assertEqual(c.post("/api/v1/runs",json={"lab_id":"lab-99"},headers=HEADERS).status_code,404)
            self.assertEqual(c.post("/api/v1/runs",json={"lab_id":"lab-01","command":"bad"},headers=HEADERS).status_code,422)
            response=c.post("/api/v1/runs",json={"lab_id":"lab-01"},headers=HEADERS)
            try:
                self.assertEqual(response.status_code,202)
                rid=response.json()["run_id"]
                self.assertEqual(c.get("/api/v1/runs/"+rid).status_code,200)
                self.assertEqual(c.get("/api/v1/runs/unknown").status_code,404)
                self.assertEqual(c.post("/api/v1/runs",json={"lab_id":"lab-01"},headers=HEADERS).status_code,409)
                self.assertTrue(c.get("/api/v1/runs").json()["blocked"])
            finally:
                release.set()
                self.wait(m)

    def test_remote_context_rejected(self):
        with patch.dict("os.environ",{},clear=True),patch("dashboard.backend.runs.subprocess.run",side_effect=[subprocess.CompletedProcess([],0,"remote\n"),subprocess.CompletedProcess([],0,"ssh://host\n")]):
            with self.assertRaises(ValueError):
                local_environment()

    def test_local_context_pinned(self):
        with patch.dict("os.environ",{},clear=True),patch("dashboard.backend.runs.subprocess.run",side_effect=[subprocess.CompletedProcess([],0,"desktop-linux\n"),subprocess.CompletedProcess([],0,"npipe:////./pipe/dockerDesktopLinuxEngine\n")]):
            self.assertEqual(local_environment()["DOCKER_CONTEXT"],"desktop-linux")
