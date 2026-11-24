import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml
from fastapi.testclient import TestClient
from dashboard.backend.main import app
from dashboard.backend.labs import discover
from tools.validate_manifest import ROOT

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = (ROOT / "labs/01-control-plane/manifest.yaml").read_text(encoding="utf-8")

    def add(self, name, raw=None, manual=True):
        folder = self.root / name
        folder.mkdir()
        (folder / "manifest.yaml").write_text(self.source if raw is None else raw, encoding="utf-8")
        if manual:
            (folder / "README.md").write_text("# Test", encoding="utf-8")
        return folder

    def test_actual_lab(self):
        result = discover()
        lab = next(l for l in result.labs if l.id == "lab-01")
        self.assertEqual([s.expected.http_status for s in lab.scenarios], [403,403,200,403,403])
        self.assertEqual(len(lab.controls),6)
        self.assertEqual(len(lab.services),4)

    def test_empty(self):
        (self.root / "manual-only").mkdir()
        self.assertEqual(discover(self.root).labs, [])
        self.assertEqual(discover(self.root).issues, [])

    def test_dynamic_discovery(self):
        self.add("first")
        self.assertEqual(len(discover(self.root).labs),1)
        self.add("second",self.source.replace("id: lab-01","id: lab-99",1))
        self.assertEqual([l.id for l in discover(self.root).labs],["lab-01","lab-99"])

    def test_invalid_isolation(self):
        self.add("valid")
        self.add("bad","secret-marker: [")
        self.add("unknown",self.source.replace("REG-01","ZZZ-99"))
        self.add("missing-manual",manual=False)
        self.add("oversized","x"*100001)
        result = discover(self.root)
        self.assertEqual(len(result.labs),1)
        self.assertEqual(len(result.issues),4)
        self.assertNotIn("secret-marker",str(result))

    def test_duplicates(self):
        self.add("first")
        self.add("second")
        result = discover(self.root)
        self.assertEqual(result.labs,[])
        self.assertEqual([i.reason for i in result.issues],["Duplicate lab ID"]*2)

    def test_linked_manifest(self):
        folder = self.add("linked")
        target = self.root / "outside.yaml"
        target.write_text(self.source,encoding="utf-8")
        (folder / "manifest.yaml").unlink()
        try:
            (folder / "manifest.yaml").symlink_to(target)
        except OSError:
            self.skipTest("Symlink creation not permitted on this platform")
        self.assertEqual(discover(self.root).labs,[])
        self.assertEqual(len(discover(self.root).issues),1)

    def test_api_list_detail_and_unknown(self):
        with TestClient(app) as client:
            response = client.get("/api/v1/labs")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers["cache-control"],"no-store")
            row = next(l for l in response.json()["labs"] if l["id"]=="lab-01")
            self.assertEqual(client.get("/api/v1/labs/lab-01").json(),row)
            self.assertEqual(client.get("/api/v1/labs/unknown").status_code,404)
            self.assertEqual(client.get("/api/v1/labs/..%2F..%2Fsecret").status_code,404)
            self.assertEqual(client.post("/api/v1/labs").status_code,405)

    def test_catalog_failure(self):
        with patch("dashboard.backend.labs.discover",side_effect=OSError("secret-marker")), TestClient(app) as client:
            response = client.get("/api/v1/labs")
            self.assertEqual(response.status_code,503)
            self.assertNotIn("secret-marker",response.text)
