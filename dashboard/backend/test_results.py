import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from dashboard.backend.main import app
from dashboard.backend.runs import Manager
from dashboard.backend.results import load_report, project_report, safe_reason, MANIFEST
from tools import evidence
from tools.validate_manifest import load_manifest

RID="a"*32
class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.report=evidence.new_run(RID,"eas-a04-"+RID)
        evidence.initialize(self.report,load_manifest(MANIFEST),MANIFEST)
        self.report["reason"]="Host port occupied: 8000"
        evidence.finish(self.report,2,time.monotonic())

    def save(self):
        return evidence.save(self.report,self.root/"evidence")

    def test_error_projection(self):
        self.save()
        view=project_report(load_report(self.root,RID))
        self.assertEqual(view.reason,"Host port occupied: 8000")
        self.assertTrue(view.manifest_matches)
        self.assertEqual(len(view.scenarios),5)
        self.assertEqual(len(view.controls),6)
        self.assertTrue(all(s.outcome=="not_run" for s in view.scenarios))

    def test_pass_projection(self):
        for s in self.report["scenarios"]:
            s.update(outcome="pass",actual=s["expected"],started_at=evidence.now(),finished_at=evidence.now(),reason="Expected status received")
        self.report.update(cleanup="success",reason="All assertions passed")
        evidence.finish(self.report,0,time.monotonic())
        self.save()
        self.assertEqual(project_report(load_report(self.root,RID)).outcome,"pass")

    def test_redaction(self):
        self.report["reason"]="secret-marker"
        self.report["scenarios"][0]["reason"]="secret-marker"
        self.assertNotIn("secret-marker",project_report(self.report).model_dump_json())
        self.assertNotEqual(safe_reason("Host port occupied: secret-marker"),"Host port occupied: secret-marker")

    def test_mismatch(self):
        self.report["project"]="other"
        self.save()
        with self.assertRaises(ValueError):
            load_report(self.root,RID)

    def test_contract(self):
        self.report["scenarios"][0]["controls"]=["REG-02"]
        with self.assertRaises(ValueError):
            project_report(self.report)

    def test_manifest_drift(self):
        self.report["manifest_sha256"]="b"*64
        self.assertFalse(project_report(self.report).manifest_matches)

    def test_oversize_traversal(self):
        path=self.save()
        path.write_bytes(b"x"*1000001)
        with self.assertRaises(ValueError):
            load_report(self.root,RID)
        with self.assertRaises(FileNotFoundError):
            load_report(self.root,"../secret")

    def test_api(self):
        path=self.save()
        m=Manager(self.root)
        with patch("dashboard.backend.runs.manager",m),TestClient(app) as c:
            url="/api/v1/runs/"+RID+"/evidence"
            response=c.get(url)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers["cache-control"],"no-store")
            self.assertEqual(c.get(url,headers={"Origin":"https://example.invalid"}).status_code,403)
            self.assertEqual(c.get("/api/v1/runs/unknown/evidence").status_code,404)
            self.assertEqual(c.post(url).status_code,405)
            path.write_text("invalid")
            self.assertEqual(c.get(url).status_code,422)

    def test_manual(self):
        with TestClient(app) as c:
            response=c.get("/api/v1/labs/lab-01/manual")
            self.assertEqual(response.status_code,200)
            self.assertIn("text/plain",response.headers["content-type"])
            self.assertIn("curl.exe",response.text)
            self.assertIn("Bash",response.text)
            self.assertEqual(c.get("/api/v1/labs/unknown/manual").status_code,404)
