"""Offline regression tests: no Docker or live network."""
import contextlib
import io
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import uuid

import httpx
from jsonschema import ValidationError
import evidence
import run_lab01 as lab
import report_evidence
from http_runner import HttpRunner, RunnerError
from validate_manifest import ROOT, load_manifest, validate

MANIFEST = ROOT / "labs/01-control-plane/manifest.yaml"

def fresh():
    manifest = load_manifest(MANIFEST)
    run_id = uuid.uuid4().hex
    run = evidence.new_run(run_id, "eas-a04-" + run_id)
    evidence.initialize(run, manifest, MANIFEST)
    return manifest, run

class ManifestTests(unittest.TestCase):
    def test_invalid_contracts(self):
        for mutation in ("unknown_control", "duplicate_id", "string_status", "extra_field"):
            with self.subTest(mutation=mutation):
                m = load_manifest(MANIFEST)
                if mutation == "unknown_control":
                    m["scenarios"][0]["controls"] = ["ZZZ-99"]
                elif mutation == "duplicate_id":
                    m["scenarios"][1]["id"] = m["scenarios"][0]["id"]
                elif mutation == "string_status":
                    m["scenarios"][0]["expected"]["http_status"] = "403"
                else:
                    m["url"] = "http://example.invalid"
                with self.assertRaises(ValueError):
                    validate(m)

    def test_unsafe_yaml(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.yaml"
            for raw in ("id: a\nid: b\n", "id: &x a\ntitle: *x\n", "x" * 100001):
                path.write_text(raw, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_manifest(path)

class HttpTests(unittest.TestCase):
    def test_redirect_not_followed(self):
        requests = []
        def handler(request):
            requests.append(request)
            if request.url.port == 8081:
                return httpx.Response(200, json={"access_token":"synthetic-secret"})
            return httpx.Response(302, headers={"Location":"https://example.invalid"})
        with HttpRunner(httpx.MockTransport(handler)) as runner:
            runner.authenticate()
            result = runner.execute("lab-01-active-read", 200)
        self.assertEqual((result.outcome, result.actual), ("fail", 302))
        self.assertEqual(len(requests), 2)

    def test_malformed_token(self):
        for token in (None, "", "bad token", 123):
            with self.subTest(token=token):
                with HttpRunner(httpx.MockTransport(lambda r: httpx.Response(200, json={"access_token":token}))) as runner:
                    with self.assertRaises(RunnerError):
                        runner.authenticate()

    def test_no_auth(self):
        with HttpRunner(httpx.MockTransport(lambda r: self.fail("unexpected request"))) as runner:
            self.assertEqual(runner.execute("lab-01-active-read", 200).outcome, "error")

class LifecycleTests(unittest.TestCase):
    def exercise(self, fault=None):
        manifest, run = fresh()
        state = None
        calls = []
        token_calls = 0
        def handler(request):
            nonlocal state, token_calls
            if request.url.port == 8081:
                token_calls += 1
                return httpx.Response(200, json={"access_token":"synthetic-secret"})
            if request.url.port == 8000:
                if request.method == "POST":
                    self.assertIn("X-Lab-Admin-Key", request.headers)
                    if fault == "transition" and request.url.path.endswith("/active"):
                        return httpx.Response(409, text="synthetic-secret")
                    state = request.url.path.split("/")[-1] if "/state/" in request.url.path else "draft"
                return httpx.Response(404 if state is None else 200, json={"lifecycle":state})
            self.assertEqual(request.headers["Authorization"], "Bearer synthetic-secret")
            calls.append((state, request.method))
            status = 200 if state == "active" and request.method == "GET" else 403
            if fault == "dependency" and state is None:
                status = 503
            if fault == "delete" and request.method == "DELETE":
                status = 200
            if fault == "expired" and state == "suspended":
                status = 401
            return httpx.Response(status, text="synthetic-secret")
        output = io.StringIO()
        with contextlib.redirect_stdout(output), HttpRunner(httpx.MockTransport(handler)) as runner:
            runner.authenticate()
            if fault == "transition":
                with self.assertRaises(RunnerError):
                    lab.run_scenarios(runner, manifest, run)
                code = 2
            else:
                code = lab.run_scenarios(runner, manifest, run)
        run["cleanup"] = "success"
        evidence.finish(run, code, time.monotonic())
        evidence.validate(run)
        self.assertEqual(token_calls, 1)
        self.assertNotIn("synthetic-secret", json.dumps(run) + output.getvalue())
        return code, [s["outcome"] for s in run["scenarios"]], calls

    def test_order_and_same_token(self):
        code, outcomes, calls = self.exercise()
        self.assertEqual(code, 0)
        self.assertEqual(outcomes, ["pass"] * 5)
        self.assertEqual(calls, [(None,"GET"),("draft","GET"),("active","GET"),("active","DELETE"),("suspended","GET")])

    def test_fail_fast(self):
        for fault, code, outcomes in [
            ("dependency",2,["error"]+["not_run"]*4),
            ("delete",1,["pass"]*3+["fail","not_run"]),
            ("expired",2,["pass"]*4+["error"]),
            ("transition",2,["pass"]*2+["error","not_run","not_run"])]:
            with self.subTest(fault=fault):
                actual, rows, _ = self.exercise(fault)
                self.assertEqual((actual, rows), (code, outcomes))

    def test_wrong_state(self):
        with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,json={"lifecycle":"draft"}))) as client:
            with self.assertRaises(RunnerError):
                lab.require_state(client, "active")

class MainTests(unittest.TestCase):
    def execute(self, fault):
        with patch("sys.argv", ["run_lab01.py"]), patch("socket.socket") as sock, patch.object(lab,"compose") as compose, patch.object(lab,"HttpRunner"), patch.object(lab,"ready"), patch.object(lab,"run_scenarios",return_value=1), patch.object(evidence,"save",return_value=Path("mock.json")) as save, contextlib.redirect_stdout(io.StringIO()):
            sock.return_value.__enter__.return_value.connect_ex.return_value = 0 if fault == "occupied" else 1
            if fault == "startup":
                compose.side_effect = [subprocess.CalledProcessError(1,["docker"]),None]
            if fault == "cleanup":
                compose.side_effect = [None,subprocess.CalledProcessError(1,["docker"])]
            if fault == "save":
                save.side_effect = OSError("synthetic-secret")
            code = lab.main()
            run = save.call_args.args[0]
            if fault == "occupied":
                compose.assert_not_called()
                self.assertEqual(run["cleanup"],"not_required")
            else:
                project = compose.call_args_list[0].args[0]
                self.assertTrue(project.startswith("eas-a04-"))
                compose.assert_called_with(project,"down","-v",timeout=120)
            return code, run

    def test_occupied(self):
        code, run = self.execute("occupied")
        self.assertEqual(code,2)
        self.assertTrue(all(s["outcome"]=="not_run" for s in run["scenarios"]))

    def test_startup_cleanup(self):
        code, run = self.execute("startup")
        self.assertEqual((code,run["cleanup"]),(2,"success"))

    def test_cleanup_failure(self):
        code, run = self.execute("cleanup")
        self.assertEqual((code,run["cleanup"]),(2,"error"))

    def test_persistence_failure(self):
        code, _ = self.execute("save")
        self.assertEqual(code,2)

class EvidenceRegression(unittest.TestCase):
    def test_inconsistent_reports(self):
        for fault in ("exit","skipped","pass","extra"):
            _, run = fresh()
            evidence.finish(run,2,time.monotonic())
            row = run["scenarios"][0]
            if fault == "exit":
                run["outcome"]="pass"
            elif fault == "skipped":
                row["actual"]=403
            elif fault == "pass":
                row.update(outcome="pass",actual=200)
            else:
                run["token"]="synthetic-secret"
            with self.subTest(fault=fault), self.assertRaises((ValueError,ValidationError)):
                evidence.validate(run)

    def test_atomic_failure_and_distinct_files(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for _ in range(2):
                _, run = fresh()
                evidence.finish(run,2,time.monotonic())
                evidence.save(run,directory)
            self.assertEqual(len(list(directory.iterdir())),2)
            _, run = fresh()
            evidence.finish(run,2,time.monotonic())
            with patch.object(evidence.os,"replace",side_effect=OSError("write failure")):
                with self.assertRaises(OSError):
                    evidence.save(run,directory)
            self.assertEqual(len(list(directory.iterdir())),2)

    def test_invalid_report_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"invalid.json"
            path.write_text("{}",encoding="utf-8")
            with patch("sys.argv",["report_evidence.py",str(path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(report_evidence.main(),2)
