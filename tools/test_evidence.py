import tempfile
import time
import unittest
from pathlib import Path
import uuid
import evidence
from validate_manifest import ROOT, load_manifest

class EvidenceTests(unittest.TestCase):
    def build(self):
        run_id = uuid.uuid4().hex
        run = evidence.new_run(run_id, "eas-a04-" + run_id)
        path = ROOT / "labs/01-control-plane/manifest.yaml"
        evidence.initialize(run, load_manifest(path), path)
        return run

    def test_blocked_run_roundtrip(self):
        run = self.build()
        evidence.finish(run, 2, time.monotonic())
        with tempfile.TemporaryDirectory() as folder:
            target = evidence.save(run, Path(folder))
            import json
            self.assertEqual(json.loads(target.read_text()), run)

    def test_success_requires_assertions(self):
        run = self.build()
        evidence.finish(run, 0, time.monotonic())
        with self.assertRaises(ValueError):
            evidence.validate(run)

    def test_success(self):
        run = self.build()
        for row in run["scenarios"]:
            row.update(outcome="pass", actual=row["expected"],
                       started_at=evidence.now(), finished_at=evidence.now(),
                       reason="Expected status received")
        run["cleanup"] = "success"
        evidence.finish(run, 0, time.monotonic())
        evidence.validate(run)

if __name__ == "__main__":
    unittest.main()
