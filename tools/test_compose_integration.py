"""Explicit opt-in only: local Docker, fixed ports must be free."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from validate_manifest import ROOT
import evidence

@unittest.skipUnless(os.getenv("EAS_RUN_INTEGRATION") == "1", "Set EAS_RUN_INTEGRATION=1 for local Docker integration")
class ComposeIntegration(unittest.TestCase):
    def test_repeatable_lifecycle(self):
        ids = set()
        for _ in range(2):
            result = subprocess.run([sys.executable,str(ROOT/"tools/run_lab01.py")],
                                    cwd=ROOT,capture_output=True,text=True,timeout=1000)
            self.assertEqual(result.returncode,0,result.stdout)
            paths = [line.removeprefix("Evidence: ") for line in result.stdout.splitlines() if line.startswith("Evidence: ")]
            self.assertEqual(len(paths),1)
            path = Path(paths[0])
            run = json.loads(path.read_text(encoding="utf-8"))
            evidence.validate(run)
            self.assertEqual(run["outcome"],"pass")
            self.assertEqual(run["cleanup"],"success")
            self.assertEqual([s["actual"] for s in run["scenarios"]],[403,403,200,403,403])
            self.assertNotIn(run["run_id"],ids)
            ids.add(run["run_id"])
            for resource in ("ps","volume","network"):
                args = ["docker",resource,"ls"] if resource != "ps" else ["docker","ps","-a"]
                check = subprocess.run(args+["--filter","label=com.docker.compose.project="+run["project"],"--format","{{.ID}}"],capture_output=True,text=True,check=True,timeout=30)
                self.assertEqual(check.stdout.strip(),"",resource+" remains")
